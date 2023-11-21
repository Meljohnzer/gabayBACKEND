from django.urls import path
from .views import *

urlpatterns = [
    path('add/',AddIncome.as_view()),
    path('income/view/<int:user>/',ShowIncome.as_view()),
    path('category/',AddCategory.as_view()),
    path('transaction/',AddTransaction.as_view()),
    path('page/<int:user>/',YourModelListView.as_view()),
    path('same/month/year/<int:user>/',GetAllTheSameMonth.as_view()),
    path('user/income/',SumIncome.as_view()),
     path('transaction-data/<int:user>/', TransactionDataView.as_view(), name='transaction-data'),
    ]