from django.shortcuts import render
from rest_framework import generics,status
from .serializers import IncomeSerializer
from .models import *
from rest_framework.response import Response


# Create your views here.
class AddIncome(generics.ListCreateAPIView):
    serializer_class  = IncomeSerializer
    queryset = Income.objects.all()

#Todo Add Request Api to call

