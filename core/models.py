from django.db import models
import django
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
import os
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
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
    phone_code = models.CharField(
        max_length=4, blank=True, null=True, default="+254")
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    avatar = models.FileField(blank=True, null=True)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default='client')
    username = models.CharField(
        max_length=128, unique=True, blank=True, null=True)
    password = models.CharField(max_length=128, default='123456')
    phone_number = models.CharField(
        max_length=10, blank=True, null=True, unique=True)
    nationality = models.CharField(max_length=30, blank=True, null=True)
    therapy_license = models.CharField(max_length=255, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(
        max_length=255, unique=True, blank=True, null=True)
    # transaction_id = models.ForeignKey(
    #     Transaction, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return self.username


TRANSACTION_STATUS_CHOICES = (
    ("processing", "Processing"),
    ("successful", "Successful"),
    ("failed", "Failed"),
)
CURRENCY_CHOICES = (
    ("Ksh", "Kenyan Shilling"),
    ("USD", "US Dollar"),
    ("UGD", "Ugandan Shilling"),
    ("TZS", "Tanzanian Shilling"),
)
TRANSACTION_TYPE_CHOICES = (
    ("donation", "Donation"),
    ("session_booking", "Session_booking"),
    ("therapist_subscription", " Therapist Subscription"),
    ("client_subscription", " Client Subscription"),

)


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    customer_account_number = models.CharField(max_length=20, null=True)
    transaction_amount = models.FloatField()
    transaction_currency = models.CharField(
        max_length=40, choices=CURRENCY_CHOICES, default="Kenyan Shilling"
    )
    transaction_identifier = models.CharField(
        max_length=255, unique=True, null=True
    )  # idempotency_key from mpesa
    transaction_code = models.CharField(
        max_length=255, unique=True, null=True
    )  # Mpesa code after a payment is complete
    transaction_type = models.CharField(
        max_length=100, choices=TRANSACTION_TYPE_CHOICES, default="session_booking")
    # user_id = models.ForeignKey(
    #         User, on_delete=models.PROTECT
    #     )  # should take the current logged in user
    transaction_status = models.CharField(
        max_length=20, choices=TRANSACTION_STATUS_CHOICES, default="successful"
    )
    # add column to specify if transaction has already been utilised
    utilised = models.BooleanField(default=False)


class BookingSession(models.Model):
    WAITING = 'waiting'
    ACCEPTED = 'accepted'
    CONDUCTED = 'conducted'

    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (CONDUCTED, 'Conducted'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_date = models.DateField()
    session_time = models.TimeField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=WAITING)
    transaction_id = models.ForeignKey(
        Transaction, on_delete=models.PROTECT, null=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Booking Session for {self.user.username} on {self.session_date} at {self.session_time} - Status: {self.status}"


class Game(models.Model):
    ROCK = 'rock'
    PAPER = 'paper'
    SCISSORS = 'scissors'

    CHOICES = [
        (ROCK, 'rock'),
        (PAPER, 'paper'),
        (SCISSORS, 'scissors'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Choices: rock, paper, scissors
    player_choice = models.CharField(max_length=10, choices=CHOICES)
    # Choices: rock, paper, scissors
    computer_choice = models.CharField(max_length=10)
    # Result of the game (e.g., "You Won!", "A Draw!", "You Lost!")
    result = models.CharField(max_length=20)
    play_again = models.BooleanField(default=True)
    # Timestamp when the game was played
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Game played by {self.user.username} at {self.created_at}"


class ChatCompletion(models.Model):
    user_input = models.TextField()
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255)
    chat_response = models.TextField()

    def __str__(self):
        return f"{self.method} request to {self.path} - User says: {self.user_input}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message}'
