from django.shortcuts import render
from django.core import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import * 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .email import send_otp
from rest_framework.views import APIView
from .serializers import (RegisterSerializer,SendEmailVerificationSerializer,
                          OTPVerificationSerializer,LoginSerializer,
                          ForgotPasswordSerializer)
from rest_framework.generics import GenericAPIView,RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from income.models import *

#Creating new account
class RegisterView(APIView):
    def post(self,request):
        data=request.data
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email = email).first()
     
        serializer.save()
        return Response(
          'Registered successfully!'
        )
#To Acces All Current User
class RegisterViewAll(generics.ListAPIView):
    serializer_class = RegisterSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset
    
#Accept Email to Send OTP
class SendEmailVerification(APIView):

    def post(self,request):
        try:
            data = request.data
            serializer = SendEmailVerificationSerializer(data=data)
            if serializer.is_valid():
                email = serializer.data['email']
                user = User.objects.filter(email = email)
                html = "email.html"
                subject = "Account One Time Pin Verification!"
                if not user.exists():
                    return Response({"Warning":"Email Is Not Registered!", "status" : status.HTTP_404_NOT_FOUND})
                if user[0].is_Verified:
                    return Response({"Warning":"Email Already Verified", "status" : status.HTTP_208_ALREADY_REPORTED})
                else:
                    send_otp(email,html,subject)
                    return Response({"Warning":"OTP Sent Successfully!", "status":status.HTTP_200_OK})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(e)
            return Response("Internal Server Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#Accepting Email And OTP to Verify Account
class OTPVerification(APIView):
    def post(self,request):
        try:
            data = request.data
            serializer = OTPVerificationSerializer(data=data)
            if serializer.is_valid():
                email = serializer.data['email']
                otp = serializer.data['otp']
                user = User.objects.filter(email = email)

                if not user.exists():
                    return Response({"Warning":{"Warning":"Email Is Not Registered!","status": status.HTTP_401_UNAUTHORIZED}, "status" : status.HTTP_404_NOT_FOUND})
                if user[0].otp != otp:
                    return Response({"Warning":"Invalid OTP!","status":status.HTTP_400_BAD_REQUEST})
                if user[0].is_Verified:
                    return Response({"Warning":"Email Already Verified", "status":status.HTTP_208_ALREADY_REPORTED})
                user = user.first()
                user.is_Verified = True
                user.save()
                return Response({"Warning":"Email Verified", "status":status.HTTP_200_OK})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
        
        except Exception as e:
            print(e)
            return Response("Internal Server Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class Login(APIView):
  def post(self,request):
    try:
        data = request.data
        serializer = LoginSerializer(data=data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = User.objects.filter(email=email).first()
            income = Income.objects.filter(user = user.id)
            user_data = {
                        "id": user.id,
                        "email": user.email,
                        # Add other fields you want to include in the response
                    }
            if not user or not check_password(password,user.password):
                return Response({"Warning":"Incorrect Email or Password","status":status.HTTP_404_NOT_FOUND})
            if not user.is_Verified:
                return Response({"status" : status.HTTP_401_UNAUTHORIZED,"Warning" : "Account Not Verified"})
            if income.exists():
                 return JsonResponse({"status" : status.HTTP_100_CONTINUE,"Warning" : "Home","user" : user_data,"bol":income.exists()})
            
            return JsonResponse({"user" : user_data ,"status": status.HTTP_200_OK,"bol":income.exists()})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
            print(e)
            return JsonResponse({"Warning":"Incorrect Email or Password", "status" : status.HTTP_500_INTERNAL_SERVER_ERROR})
    

class SendEmailForgotVerification(APIView):
    def post(self,request):
        try:
            data = request.data
            serializer = SendEmailVerificationSerializer(data=data)
            if serializer.is_valid():
                email = serializer.data['email']
                user = User.objects.filter(email = email)
                html = "passwmail.html"
                subject = "Forgotten Password Account One Time Pin Verification!"
                if not user.exists():
                    return Response({"Warning":"Email Is Not Registered!","status": status.HTTP_401_UNAUTHORIZED})
                else:
                    send_otp(email,html,subject)
                    return Response({"Warning":"OTP Sent Successfully!", "status":status.HTTP_200_OK})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(e)
            return Response("Internal Server Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NewPassword(generics.RetrieveUpdateAPIView):
    serializer_class = ForgotPasswordSerializer
    queryset = User.objects.all()
    lookup_field = "email"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        # Hash the new password before saving it
        validated_data = serializer.validated_data
        new_password = validated_data.get('password')
        hashed_password = make_password(new_password)
        instance.password = hashed_password
        instance.save()

        return Response(serializer.data)