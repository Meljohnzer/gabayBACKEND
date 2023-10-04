from django.shortcuts import render
from django.core import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import * 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import generics,status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .email import send_otp
from rest_framework.views import APIView
from .serializers import (RegisterSerializer,SendEmailVerificationSerializer,OTPVerificationSerializer,LoginSerializer)
from rest_framework.generics import GenericAPIView,RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

#Creating new account
class RegisterView(APIView):
    def post(self,request):
        data=request.data
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # send_otp(serializer.data['email'])
        # queryset = User.objects.all()
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

                if not user.exists():
                    return Response("Email Is Not Registered!")
                else:
                    send_otp(email)
                    return Response("OTP Sent Successfully!", status=status.HTTP_200_OK)
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
                    return Response("Email Is Not Registered!")
                if user[0].otp != otp:
                    return Response("Invalid OTP!",status=status.HTTP_400_BAD_REQUEST)
                if user[0].is_Verified:
                    return Response("Email Already Verified", status=status.HTTP_208_ALREADY_REPORTED)
                user = user.first()
                user.is_Verified = True
                user.save()
                return Response("Email Verified", status=status.HTTP_200_OK)
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
            user = User.objects.filter(email=email)
            
            if not user.exists() or not check_password(password,user[0].password):
                return Response("Incorrect Email or Password",status=status.HTTP_404_NOT_FOUND)
            if not user[0].is_Verified:
                return Response({"status" : status.HTTP_401_UNAUTHORIZED,"Warning" : "Account Not Verified"},status=status.HTTP_401_UNAUTHORIZED)
            user_data = {
                        "id": user[0].id,
                        "email": user[0].email,
                        # Add other fields you want to include in the response
                    }
            return JsonResponse({"user" : user_data ,"status": status.HTTP_200_OK})
        else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
            print(e)
            return Response("Internal Server Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)