from django.urls import path
from .views import *

urlpatterns = [
    path('add/',AddIncome.as_view()),
    
    ]