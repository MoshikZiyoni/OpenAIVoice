from rest_framework import serializers
from .models import Call, Conversation

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'text', 'is_ai', 'timestamp']

class CallSerializer(serializers.ModelSerializer):
    conversation_turns = ConversationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Call
        fields = ['id', 'phone_number', 'caller_id', 'prompt', 'voice', 'status', 
                  'created_at', 'updated_at', 'call_sid', 'duration', 'conversation_turns']
        read_only_fields = ['status', 'created_at', 'updated_at', 'call_sid', 'duration']

class CreateCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ['phone_number', 'caller_id', 'prompt', 'voice']
    
    def validate_phone_number(self, value):
        # Validate phone number format (basic validation)
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must include country code and start with '+'")
        return value
    
    def validate_caller_id(self, value):
        # Validate caller ID format (only allow Israeli numbers)
        if not value.startswith('+972'):
            raise serializers.ValidationError("Caller ID must be an Israeli number starting with '+972'")
        return value