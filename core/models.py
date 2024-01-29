from django.db import models
import django
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
import os
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from django.utils import timezone

# Create your models here.

phone_validator = RegexValidator(r"^\d{9,10}$", "Enter a valid phone number.")

phone_code_validator = RegexValidator(r"^\+\d{1,3}$")

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_code = models.CharField(
        max_length=4, validators=[phone_code_validator], blank=True, null=True , default= "+254"
    )
    first_name = models.CharField(max_length= 30, blank=True, null= True)
    last_name = models.CharField(max_length = 30, blank= True, null= True)
    avator = models.FileField(blank=True, null= True)
    username = models.CharField(max_length = 128, unique =True,  default = 'admin')
    password = models.CharField(max_length=128, default='123456')
    phone_number = models.CharField(
        max_length=10, validators=[phone_validator], blank=True, null=True, unique=True
    )

class Therapist(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    reg_number = models.CharField(max_length=255, unique=True)
    nationality = models.CharField(max_length=30)
    email = models.EmailField( unique= True, blank= False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class ChatCompletion(models.Model):
    user_input = models.TextField()
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255)
    chat_response = models.TextField()

    def __str__(self):
        return f"{self.method} request to {self.path} - User says: {self.user_input}"

