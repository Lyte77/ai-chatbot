# chat/urls.py (create this file)

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    path('stream/', views.chat_stream, name='chat_stream'), 
    path('clear_history/', views.clear_history, name='clear_history'),
]

