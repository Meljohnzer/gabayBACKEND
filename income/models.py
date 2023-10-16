from django.db import models
from userauth.models import User

# Create your models here.
class Income(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    title = models.CharField(max_length=64)
    amount = models.IntegerField()


class Category(models.Model):
    title = models.CharField(max_length=64)

class Transaction(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    amount = models.IntegerField()
    icon = models.CharField(max_length=125)
    description = models.TextField()
    date = models.DateField()