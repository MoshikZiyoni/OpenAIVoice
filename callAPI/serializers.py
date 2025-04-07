from rest_framework import serializers
from .models import Call

class CallSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.ReadOnlyField()
    formatted_updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = Call
        fields = ['id', 'phone_number', 'caller_id', 'status', 'call_sid', 
                  'total_duration', 'conversation', 'direction', 
                  'formatted_created_at', 'formatted_updated_at']