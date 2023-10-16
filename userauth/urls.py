from django.urls import path
from .views import *

urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('user/',RegisterViewAll.as_view()),
    path('otp/',SendEmailVerification.as_view()),#use also in forgot password end point to verify the otp!!
    path('verify/',OTPVerification.as_view()),
    path('login/',Login.as_view()),
    path('otp/reset/password/',SendEmailForgotVerification.as_view()),
    
    ]