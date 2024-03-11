from rest_framework import serializers
from .models import *
from django.db.models import Sum

class IncomeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Income
        fields = '__all__'

class EditIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ['title','amount']
class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
class EditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['description','amount']
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
    key = serializers.CharField(source='title')
    value = serializers.IntegerField(source='amount')
    class Meta:
        model = Income
        fields = ['id','total_sum','key','value','icon']

    def get_total_sum(self, obj):
        queryset = Income.objects.filter(user=obj.user)
        total_amount = queryset.aggregate(total_amount=Sum('amount'))['total_amount']
        return total_amount


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['user','date', 'category', 'icon','description','amount']


class SendMailSerializer(serializers.Serializer):
    from_email = serializers.EmailField()
    subject = serializers.CharField()
    message = serializers.CharField()

class FixSavingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fixsaving
        fields = '__all__'