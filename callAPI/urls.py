from django.urls import path
from . import views

urlpatterns = [
    path('call/', views.make_call, name='make-call'),
    path('call/<str:call_id>/twiml/', views.call_twiml, name='call-twiml'),
    path('call/<str:call_id>/status/', views.call_status, name='call-status'),
    path('calls/', views.get_calls, name='get-calls'),
    path('call/<str:call_id>/conversation/', views.get_conversation, name='get-conversation'),
    path('partial-callback/', views.partial_callback, name='partial_callback'),
   
]
