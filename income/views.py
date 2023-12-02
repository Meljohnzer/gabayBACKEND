from django.shortcuts import render
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle,Spacer,Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.core.mail import send_mail
from django.db.models import Sum
from django.conf import settings
from rest_framework import generics,status
from .serializers import (IncomeSerializer,
                          CategorySerializer,
                          EditIncomeSerializer,
                          EditTransactionSerializer,
                          TransactionSerializer,
                          YourGroupedDataSerializer,
                          DateSerializer,
                          SendMailSerializer,
                          NewTransactionSerializer,
                          SumIncomeSerializer,
                          TransactionSerializer)
from .models import *
from django.db.models import Count
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.http import JsonResponse
from rest_framework.views import APIView
import pandas as pd
import numpy as np
import io
from itertools import groupby
from operator import itemgetter
from datetime import datetime



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
        queryset = Transaction.objects.values('date').annotate(count=Count('id')).filter(user=user).order_by('date')
        

        return queryset
    
class SumIncome(generics.ListAPIView):
    serializer_class = SumIncomeSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.query_params.get('user')

        queryset = Income.objects.filter(user=user)
        total_amount = queryset.aggregate(total_amount=Sum('amount'))['total_amount']
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({'total_amount': total_amount,'data':serializer.data})
def map_category(category_id):
    # You may need to adjust this based on your actual Category model structure
        category_mapping = {
        1: "Necessities",
        2: "Wants",
        3: "Savings",
    }
        return category_mapping.get(category_id, "Unknown")
    
class TransactionDataView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.kwargs.get('user')
        # Return the queryset of Transaction objects
        
        return Transaction.objects.all().filter(user=user)

    def list(self, request, *args, **kwargs):
        user = self.kwargs.get('user', None)
        transaction = Transaction.objects.all().filter(user=user)
        user_income = Income.objects.all().filter(user=user)

        queryset = self.get_queryset()

        period = self.request.query_params.get('period')
        choice = self.request.query_params.get('choice')
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

        # pdf -0808
        pdf_buffer = io.BytesIO()
        response = HttpResponse(pdf_buffer.read(),content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Gabay_report.pdf"'

        # Create a PDF document
        
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

        title = "Transaction Reports"
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        doc_title = Paragraph(title, title_style)

        months = ""
        months_title = Paragraph(months,title_style)
        income_title = "Income Reports"
        income_doc_title = Paragraph(income_title, title_style)

        
        average_title = "Average Reports"
        average_doc_title = Paragraph(average_title, title_style)

        forecast_title = "Forcast Reports"
        forecast_doc_title = Paragraph(forecast_title, title_style)

        # Create a table and set its style
        transaction_jSON = []
        table_data = [['Date', 'Category', 'Description', 'Amount']]
        for transactions in transaction:
            data = TransactionSerializer(transactions).data
            date_str = data['date']
            user_id = data['user']
            category_id = data['category']
            icon_id = data['icon']
            description = data['description']
            amount = data['amount']

            category_label = map_category(category_id)

            transaction_jSON.append({'date':date_str, "category":category_label, "description":description, "amount":"P {:,.2f}".format(amount)})
            
        sorted_transactions = sorted(transaction_jSON, key=itemgetter('date'))

        grouped_by_month = {month: list(group) for month, group in groupby(sorted_transactions, key=lambda x: x['date'])}

        content  = []

        for month, transactions_group in grouped_by_month.items():
            # content.append(f"{month}\n{'_' * 30}\n\n")
            # Create a table for each month
            parse_data = datetime.strptime(month, "%Y-%m-%d")
            long = parse_data.strftime("%B %Y")
            print(months)
            month_table_data = [["","",f"{long}","",""],['Category', "",'Description',"", 'Amount']]
            total_amount_sum = 0
            for transaction in transactions_group:
                date_str = transaction['date']
                category_label = transaction['category']
                description = transaction['description']
                amount = transaction['amount']

                month_table_data.append([category_label,"",description,"", amount])

                amount_value = float(amount.split()[1].replace(',', ''))
                total_amount_sum += amount_value
            month_table_data.append(["Total Amount", "", "", "","P {:,.2f}".format(total_amount_sum)])
            month_table_data.append([''])

            
            transaction_table = Table(month_table_data, colWidths=100, rowHeights=25)
            transaction_table.setStyle(TableStyle([
            # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR',  (0, 1), (-1, 1), colors.red),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#3A6B35')),
            # ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border above the header row
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border below the header row
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),# Add a horizontal border to the data rows
            # ('BACKGROUND', (-1, 0), (-1, -1), colors.grey),  
            ('BACKGROUND', (0, -2), (-1, -2), colors.grey),
            ('BOTTOMPADDING', (0, -2), (-1, -2), 6),
            ]))

            content.append(transaction_table)
            # content.append("\n\n")
        
        
        
        table_data = [['Title', 'Amount']]
        income_sum = 0
        for incomes in user_income:
            data = IncomeSerializer(incomes).data
            Title = data['title']
            amount = data['amount']
            
            table_data.append([Title,"P {:,.2f}".format(amount)])
            income_value = float(amount)
            income_sum += income_value
        table_data.append(["Total Amount","P {:,.2f}".format(income_sum)])

        income_table = Table(table_data, colWidths=200, rowHeights=25)
        income_table.setStyle(TableStyle([
            # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border above the header row
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border below the header row
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),  # Add a horizontal border to the data rows
        ]))
        print(income_table)
        table_data = [['Category', 'Average']]
        for average in results_list:
            label = average['key']
            amount = average['value']

            table_data.append([label,"P {:,.2f}".format(amount)])

        average_table = Table(table_data, colWidths=200, rowHeights=25)
        average_table.setStyle(TableStyle([
            # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border above the header row
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border below the header row
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),  # Add a horizontal border to the data rows
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ]))


        table_data = [[f'No of {period}(s)', 'Predicted Savings']]

        table_data.append([no_months_to_predict,"P {:,.2f}".format(predicted_sums_per_category[3].sum())])

        forecast_table = Table(table_data, colWidths=200, rowHeights=25)
        forecast_table.setStyle(TableStyle([
            # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border above the header row
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border below the header row
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),  # Add a horizontal border to the data rows
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ]))

        

        # Build the PDF document


        
        doc.build([income_doc_title,income_table,doc_title,months_title, *content,average_doc_title,average_table,forecast_doc_title,forecast_table])

        pdf_value = pdf_buffer.getvalue()

        response.write(pdf_value)

        # pdf
        
        # print(df)
        # Return the serialized data as JSON response
        if choice == "PDF":
            return response
        else:
            return Response({"avarage" : results_list,"forecast":predicted_sums_per_category[3].sum()})

class SendEmailRS(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SendMailSerializer(data=request.data)

        if serializer.is_valid():
            type = self.request.query_params.get('type')
            from_email = serializer.validated_data['from_email']
            subject = serializer.validated_data['subject']
            message = serializer.validated_data['message']
            to_email = settings.EMAIL_HOST_USER
            host = settings.EMAIL_HOST
            if type == "Report":
                email_content = render_to_string('reportmail.html', {'subject': subject, 'message': message,'email' : from_email})
            else:
                email_content = render_to_string('supportmail.html', {'subject': subject, 'message': message,'email' : from_email})
            # Assuming you have configured your email settings in settings.py
            send_mail(subject, message, from_email, [to_email], fail_silently=False)
            send_mail(subject, "", host, [from_email],html_message=email_content, fail_silently=False)
        
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GeneratePDFView(APIView):
    
    
    def get(self, request, *args, **kwargs):
        user = self.kwargs.get('user', None)
        transaction = Transaction.objects.all().filter(user=user)
        user_income = Income.objects.all().filter(user=user)

        # Create a response object with PDF content type
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="income_report.pdf"'

        # Create a PDF document
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

        title = "Transaction Reports"
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        doc_title = Paragraph(title, title_style)

        income_title = "Income Reports"
        income_doc_title = Paragraph(income_title, title_style)

        # Create a table and set its style
        table_data = [['Date', 'Category', 'Description', 'Amount']]
        for transactions in transaction:
            data = TransactionSerializer(transactions).data
            date_str = data['date']
            user_id = data['user']
            category_id = data['category']
            icon_id = data['icon']
            description = data['description']
            amount = data['amount']

            category_label = map_category(category_id)

            table_data.append([date_str, category_label, description, amount])
            

        transaction_table = Table(table_data, colWidths=100, rowHeights=25)
        transaction_table.setStyle(TableStyle([
            # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#3A6B35')),
            # ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border above the header row
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border below the header row
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),# Add a horizontal border to the data rows
        ]))
        
        table_data = [['Title', 'Amount']]
        for incomes in user_income:
            data = IncomeSerializer(incomes).data
            Title = data['title']
            amount = data['amount']

            table_data.append([Title,amount])

        income_table = Table(table_data, colWidths=200, rowHeights=25)
        income_table.setStyle(TableStyle([
            # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border above the header row
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a horizontal border below the header row
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),  # Add a horizontal border to the data rows
        ]))

        # Build the PDF document
        
        doc.build([doc_title, transaction_table,income_doc_title,income_table])

        pdf_value = pdf_buffer.getvalue()

        response.write(pdf_value)

        return response