from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,BaseUserManager,PermissionsMixin)
import os
# Create your models here.
class UserManager(BaseUserManager):  
    def create_user(self,email,password='none'):
        if not email:
            raise ValueError('Email is not valid')
        email = self.normalize_email(email)
        user = self.model(email = email)
        user.set_password(password)
        user.save()
        return user

class User(AbstractBaseUser,PermissionsMixin):
    email= models.EmailField(max_length=255,unique=True)
    is_Verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    otp = models.TextField(blank=True,null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']

    objects = UserManager()

    def __str__(self):
        return self.email