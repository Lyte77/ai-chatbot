# ai_chat/services.py

from langchain_google_genai import ChatGoogleGenerativeAI
from typing import AsyncGenerator
import asyncio
import environ
import os
from google import genai


env = environ.Env()
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

# class AIChatService:
#     def __init__(self):
#         self.model = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash",          # fast & free-tier friendly
#             google_api_key=env("GEMINI_API_KEY"),
#             temperature=0.7,
#             max_tokens=500,
#         )
       
   
def get_ai_response(user_message: str) -> str:
    """
    Sends a message to Gemini and returns the response text.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_message,
    )
    return response.text


async def stream_ai_response(user_message: str) -> AsyncGenerator[str, None]:
    """
    Uses a queue to bridge sync Gemini chunks into an async generator.
    Each chunk is placed into the queue as soon as Gemini produces it,
    then immediately yielded to the browser — true word-by-word streaming.
    """
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def producer():
        """
        Runs in a background thread.
        Pulls chunks from Gemini and puts them in the queue immediately.
        """
        try:
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=user_message,
            )
            for chunk in response:
                if chunk.text:
                    # put_nowait is thread-safe with asyncio queues
                    loop.call_soon_threadsafe(queue.put_nowait, chunk.text)
        finally:
            # Always signal completion, even if an error occurred
            loop.call_soon_threadsafe(queue.put_nowait, None)

    # Start producer in a background thread — doesn't block async loop
    loop.run_in_executor(None, producer)

    # Consume from queue as chunks arrive
    while True:
        chunk_text = await queue.get()

        if chunk_text is None:
            # None is our signal that streaming is done
            yield "data: [DONE]\n\n"
            break

        yield f"data: {chunk_text}\n\n"