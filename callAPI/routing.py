# callAPI/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^wss/openai_voice/$', consumers.OpenAIVoiceConsumer.as_asgi()),
]
