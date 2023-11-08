from django.shortcuts import render
from django.db.models import Sum
from rest_framework import generics,status
from .serializers import (IncomeSerializer,
                          CategorySerializer,
                          TransactionSerializer,
                          YourGroupedDataSerializer,
                          DateSerializer,
                          NewTransactionSerializer,
                          SumIncomeSerializer)
from .models import *
from django.db.models import Count
from rest_framework.response import Response
from django.core.paginator import Paginator


# Create your views here.
class AddIncome(generics.ListCreateAPIView):
    serializer_class  = IncomeSerializer
    queryset = Income.objects.all()

#Todo Add Request Api to call
class ShowIncome(generics.RetrieveAPIView):
    serializer_class = IncomeSerializer
    queryset = Income.objects.all()
    lookup_field = "user"

class AddCategory(generics.ListCreateAPIView):
    serializer_class  = CategorySerializer
    queryset = Category.objects.all()


# class AddTransaction(generics.ListCreateAPIView):
#     serializer_class = TransactionSerializer
#     queryset = Transaction.objects.all()

class AddTransaction(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        # Group the data by the 'date' field and annotate it with the count of transactions
        queryset = Transaction.objects.annotate(transaction_count=Count('id'))
        return queryset

    def perform_create(self, serializer):
        user = serializer.validated_data['user']
        category = serializer.validated_data['category']
        date = serializer.validated_data['date']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data['description']

        # Check if a transaction with the same user, category, date, and description exists
        existing_transaction = Transaction.objects.filter(user=user, category=category, date=date, description=description).first()

        if existing_transaction:
            # If the transaction with the same description exists, update the amount
            existing_transaction.amount += amount
            existing_transaction.save()
            return existing_transaction
        else:
            # If no existing transaction with the same description found, create a new one
            serializer.save()
    
class YourModelListView(generics.ListAPIView):
    serializer_class = NewTransactionSerializer
    items_per_page = 10

    def get_queryset(self):
        # Extract month and year from query parameters
        # month = self.request.query_params.get('month')
        date = self.request.query_params.get('date')
        user = self.kwargs.get('user')
        
        # Get objects for the specified month and year, order by date
        queryset = Transaction.objects.filter(date=date,user = user).order_by('date')
        
        # Create a paginator object
        paginator = Paginator(queryset, self.items_per_page)
        
        # Get the requested page number from the query parameters
        page_number = self.request.query_params.get('page')
        
        try:
            # Get the specified page
            page = paginator.page(page_number)
        except Exception as e:
            # If an invalid page number is specified, return the first page
            page = paginator.page(1)
        
        return page
    
class GetAllTheSameMonth(generics.ListAPIView):
    serializer_class = DateSerializer

    def get_queryset(self):
        user = self.kwargs.get('user')
        # Group data by month and year and annotate with count
        queryset = Transaction.objects.values('date').annotate(count=Count('id')).filter(user=user)
        

        return queryset
    
class SumIncome(generics.ListAPIView):
    serializer_class = SumIncomeSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.query_params.get('user')

        queryset = Income.objects.filter(user=user)
        total_amount = queryset.aggregate(total_amount=Sum('amount'))['total_amount']
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({'total_amount': total_amount,'data':serializer.data})