"""
ASGI config for OpenAIVoice project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import callAPI.routing

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenAIVoice.settings')

# # application = get_asgi_application()
# application = ProtocolTypeRouter({
#     'http': get_asgi_application(),
#     'websocket': AuthMiddlewareStack(
#         URLRouter(
#             callAPI.routing.websocket_urlpatterns
#         )
#     ),
# })



import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path,re_path
from callAPI.views import MediaStreamConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenAIVoice.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r'media-stream', MediaStreamConsumer.as_asgi()),
        ])
    ),
})