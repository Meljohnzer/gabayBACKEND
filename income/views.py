from django.shortcuts import render
from django.db.models import Sum
from rest_framework import generics,status
from .serializers import (IncomeSerializer,
                          CategorySerializer,
                          EditIncomeSerializer,
                          EditTransactionSerializer,
                          TransactionSerializer,
                          YourGroupedDataSerializer,
                          DateSerializer,
                          NewTransactionSerializer,
                          SumIncomeSerializer,
                          TransactionSerializer)
from .models import *
from django.db.models import Count
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.http import JsonResponse
import pandas as pd
import numpy as np



# Create your views here.
class AddIncome(generics.ListCreateAPIView):
    serializer_class  = IncomeSerializer
    # queryset = Income.objects.all()
    def get_queryset(self):
        # Group the data by the 'date' field and annotate it with the count of transactions
        queryset = Income.objects.annotate(transaction_count=Count('id'))
        return queryset
    def perform_create(self, serializer):
        user = serializer.validated_data['user']
        title = serializer.validated_data['title']
        amount = serializer.validated_data['amount']

        # Check if a transaction with the same user, category, date, and description exists
        existing_transaction = Income.objects.filter(user=user, title=title).first()

        if existing_transaction:
            # If the transaction with the same description exists, update the amount
            existing_transaction.amount += amount
            existing_transaction.save()
            return existing_transaction
        else:
            # If no existing transaction with the same description found, create a new one
            serializer.save()
class EditIncome(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EditIncomeSerializer
    queryset = Income.objects.all()
    lookup_field = "pk"

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

class EditTransaction(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EditTransactionSerializer
    queryset = Transaction.objects.all()
    lookup_field = "pk"
    
class YourModelListView(generics.ListAPIView):
    serializer_class = NewTransactionSerializer
    items_per_page = 20

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
    
class TransactionDataView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.kwargs.get('user')
        # Return the queryset of Transaction objects
        
        return Transaction.objects.all().filter(user=user)

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        period = self.request.query_params.get('period')
        no_months_to_predict = int(self.request.query_params.get('no_months_to_predict'))
        income = int(self.request.query_params.get('income'))

        if period == "Year":
            no_months_to_predict *= 12

        # Serialize the queryset
        # print(no_months_to_predict)
        serializer = self.get_serializer(queryset, many=True)

        df = pd.DataFrame(serializer.data)
        df['date'] = pd.to_datetime(df['date'])
        # Handle missing values (you can choose to use different methods)
        # For example, forward-fill to replace missing values
        df['amount'].ffill(inplace=True)

        # Set the index as the 'date' column
        df.set_index('date', inplace=True)

        # Group the data by 'category', 'title', and 'date' to get the sum of amounts for each category in each month
        ts_data = df.groupby([pd.Grouper(freq='M'), 'category', 'description'])['amount'].sum().reset_index()

        # Pivot the table to have 'category' as columns
        
        pivot_table = ts_data.pivot(index='date', columns=['category', 'description'], values='amount')
        
        predicted_sums_per_category = {}

        sum_of_all_categories = income - pivot_table.sum(axis=1)

# Reindex sum_of_all_categories to match the index of pivot_table
        sum_of_all_categories = sum_of_all_categories.reindex(pivot_table.index)
        # sum_of_all_categories_array = sum_of_all_categories.to_numpy()
        # nan_values_mask = pd.isna(pivot_table[3]).to_numpy()

# Fill NaN values in pivot_table with the corresponding values from sum_of_all_categories
        print(df)
        if (3, '') not in pivot_table.columns:
            pivot_table[(3, '')] = 0
            pivot_table.loc[:, (3, '')] = pivot_table.loc[:, (3, '')].fillna(0, axis=0)
            pivot_table[(3, 'Unique')] = sum_of_all_categories


        print(pivot_table)
        results_list = []

        # num_categories = len(pivot_table.columns.levels[0])
        # weights = np.linspace(0.1, 1.0, num_categories)
        # weights /= weights.sum() 
        for category in pivot_table.columns.levels[0]:
            print(f"WEIGHTED MOVING AVERAGE FORECAST '{category}'")

    # Select the specific category from the pivot table
            ts = pivot_table[category]

    # Calculate weighted moving average with weights [0.5, 0.3, 0.2]
            # weights = np.array([0.6, 0.2, 0.2])
            weights = np.linspace(0.1, 1, len(ts))  # Example: linearly increasing weights
            weights /= weights.sum()  # Normalize weights to ensure they sum to 1
            print(weights)
            weighted_avg = np.convolve(ts.sum(axis=1), weights[::-1], mode='valid')

   
            forecast = weighted_avg[-1]  # Use the last available weighted moving average value as the forecast

   
            predicted_sum = pd.Series([forecast] * int(no_months_to_predict), index=pd.date_range(start=ts.index[-1] + pd.offsets.MonthEnd(), periods=int(no_months_to_predict), freq='M'))

            print(f"Predicted sum for '{category}' for each predicted month:")
            print(predicted_sum.mean())
            mean_predicted_sum = predicted_sum.mean()
            category_labels = {1: 'Necessities', 2: 'Wants', 3: 'Savings'}
            results_list.append({
                'key': category_labels.get(category, f'Category_{category}'),
                'value': mean_predicted_sum.tolist()  # Convert to list to handle numpy types in JSON
            })

    # Store the predictions in the dictionary for this category
            predicted_sums_per_category[category] = predicted_sum

            print()

# Sum the equal months for all categories
        sum_of_equal_months = pd.DataFrame(predicted_sums_per_category).sum(axis=1)

        print("Sum of equal months for all categories:")
        print(sum_of_equal_months)

# print("Average of total predicted sums for all categories:")
# print(average_per_month)

# Here, use the numeric value '3' instead of the variable category
        print("Total saving that will be achieved in that time:")
        print(predicted_sums_per_category[3].sum())
        
        # print(df)
        # Return the serialized data as JSON response
        return Response({"avarage" : results_list,"forecast":predicted_sums_per_category[3].sum()})