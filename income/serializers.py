from rest_framework import serializers
from .models import *

class IncomeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Income
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class NewTransactionSerializer(serializers.ModelSerializer):
    key = serializers.CharField(source='description')
    value = serializers.IntegerField(source='amount')
    class Meta:
        model = Transaction
        fields = '__all__'


class YourGroupedDataSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    count = serializers.IntegerField()

    class Meta:
        fields = '__all__'

class DateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Transaction
        fields = ['date']

class SumIncomeSerializer(serializers.ModelSerializer):
    total_sum  = serializers.SerializerMethodField()

    class Meta:
        model = Income
        fields = '__all__'