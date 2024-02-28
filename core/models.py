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
    CLIENT = 'client'
    THERAPIST = 'therapist'
    USER_TYPE_CHOICES = [
        (CLIENT, 'Client'),
        (THERAPIST, 'Therapist'),
    ]
    
    email = models.EmailField(unique=True)
    phone_code = models.CharField(max_length=4, blank=True, null=True, default="+254")
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    avatar = models.FileField(blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default = 'client')
    username = models.CharField(max_length=128, unique=True, blank= True, null= True)
    password = models.CharField(max_length=128, default='123456')
    phone_number = models.CharField(max_length=10, blank=True, null=True, unique=True)
    nationality = models.CharField(max_length=30, blank=True, null=True)
    therapy_license = models.CharField(max_length=255, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    reg_number = models.CharField(max_length=255, unique=True, blank=True, null=True)

    def __str__(self):
        return self.username

class BookingSession(models.Model):
    WAITING = 'waiting'
    ACCEPTED = 'accepted'
    CONDUCTED = 'conducted'

    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (ACCEPTED, 'Accepted'),
        (CONDUCTED, 'Conducted'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_date = models.DateField()
    session_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=WAITING)
    # Add more fields as needed
    
    def __str__(self):
        return f"Booking Session for {self.user.username} on {self.session_date} at {self.session_time} - Status: {self.status}"

class ChatCompletion(models.Model):
    user_input = models.TextField()
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255)
    chat_response = models.TextField()

    def __str__(self):
        return f"{self.method} request to {self.path} - User says: {self.user_input}"

