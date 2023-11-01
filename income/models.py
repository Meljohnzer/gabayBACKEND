from django.db import models
from userauth.models import User

# Create your models here.
class Income(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    title = models.CharField(max_length=64)
    amount = models.IntegerField()
    icon = models.CharField(null=True,max_length=124)
    color = models.CharField(max_length=124,null=True)


class Category(models.Model):
    title = models.CharField(max_length=64)

class Transaction(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    amount = models.IntegerField()
    icon = models.CharField(max_length=125,null=True)
    description = models.TextField()
    date = models.DateField()
    color = models.CharField(max_length=124,null=True)