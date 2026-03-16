
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse,StreamingHttpResponse
from django.views.decorators.http import require_POST,require_GET

from .services import get_ai_response, stream_ai_response
from .models import Message

def index(request: HttpRequest) -> HttpResponse:
    """Renders the main chat page."""
    messages = Message.objects.all()
    return render(request, 'ai_chat/chat.html', {
        'messages': messages,
    })



@require_POST  # only accept POST requests
def chat(request: HttpRequest) -> HttpResponse:
    """
    Receives a user message via HTMX POST.
    Calls the AI service.
    Returns an HTML snippet (not a full page).
    """
    user_message = request.POST.get('message', '').strip()

    if not user_message:
        return HttpResponse('<p>Please enter a message.</p>')

    ai_response = get_ai_response(user_message)

    # Return a small HTML snippet — HTMX will inject this into the page
    return render(request, 'ai_chat/partials/response.html', {
        'user_message': user_message,
        'ai_response': ai_response,
    })


@require_GET
async def chat_stream(request: HttpRequest) -> StreamingHttpResponse:
    """
    Streaming endpoint. Browser connects via EventSource.
    Stays open and pushes chunks as Gemini generates them.
    """
    user_message = request.GET.get('message', '').strip()

    if not user_message:
        return HttpResponse('No message provided.', status=400)

    # StreamingHttpResponse takes a generator — it writes each yielded
    # value to the response as it's produced, without buffering.
    response = StreamingHttpResponse(
        # stream_ai_response(user_message),
         save_and_stream(user_message),
        content_type='text/event-stream',  # tells browser this is SSE
    )
    # These headers prevent proxies/browsers from buffering the stream
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response



async def save_and_stream(user_message: str):
    """
    Wraps the stream generator.
    Collects the full response as chunks arrive,
    then saves to database after streaming completes.
    """
    from django.db import connection
    full_response = []  # collect chunks here

    async for chunk in stream_ai_response(user_message):
        yield chunk  # send to browser immediately

        # Extract just the text from the SSE format
        # chunk looks like "data: Hello\n\n" — we want "Hello"
        if chunk.startswith('data:') and chunk.strip() != 'data: [DONE]':
            text = chunk.removeprefix('data: ').strip()
            full_response.append(text)

    # Streaming done — save the complete exchange to database
    from asgiref.sync import sync_to_async
    save_message = sync_to_async(Message.objects.create)  
    await save_message(
        user_message=user_message,
        ai_response=''.join(full_response),  
    )   

@require_POST
def clear_history(request):
     messages = Message.objects.all()
     messages.delete()  
     return  HttpResponse("")