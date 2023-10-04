from rest_framework import serializers
from .models import *

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=16,min_length=8)

    class Meta:
        model = User
        fields = '__all__'
    
 
    
    def create(self,validated_data):
        return User.objects.create_user(**validated_data)
    

class SendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=16,min_length=8)



