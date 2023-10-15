from django.db import models
from userauth.models import User

# Create your models here.
class Income(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    title = models.CharField(max_length=64)
    amount = models.IntegerField()

