from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('call/', views.make_call, name='make-call'),
    # path('call/<str:call_id>/twiml/', views.call_twiml, name='call-twiml'),
    # path('call/<str:call_id>/status/', views.call_status, name='call-status'),
    # path('calls/', views.get_calls, name='get-calls'),
    # path('call/<str:call_id>/conversation/', views.get_conversation, name='get-conversation'),
    # path('partial-callback/', views.partial_callback, name='partial_callback'),
    # path('process_audio/', views.process_audio, name='process_audio'),
    # path('incoming-call/', views.incoming_call, name='incoming_call'),
    path('incoming-call/', views.handle_incoming_call, name='incoming-call'),
    path('outbound-call/', views.make_outbound_call, name='outbound-call'),
    path('', views.index_page, name='index'),
    path('call-status/', views.call_status_callback, name='call_status_callback'),
    # REST API endpoints
    path('api/calls/', views.get_calls, name='get-calls'),
    path('api/calls/<int:call_id>/', views.get_call_detail, name='get-call-detail'),
    path('api/calls/stats/', views.get_call_stats, name='get-call-stats'),
    path('api/calls/outbound/', views.initiate_outbound_call, name='initiate-outbound-call'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
