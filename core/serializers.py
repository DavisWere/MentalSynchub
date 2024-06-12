import os
import datetime
from datetime import timedelta
from django.utils.timezone import make_aware
import requests
import pywhatkit
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction
from django.db.models import Sum
import json
from django.conf import settings
from .google_api import create_google_meet_event
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from core.models import (User,  BookingSession,
                         Transaction, Game, ChatCompletion, Notification,
                         Schedule)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["is_superuser"] = user.is_superuser
        return token

# serializers.py


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'user_type',  'first_name', 'last_name', 'email', 'phone_code',
                  'phone_number', 'nationality', 'avatar', 'therapy_license',
                  'specialization', 'license_number', 'username', 'password'
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assuming user_type is passed in request data
        user_type = self.context['request'].data.get('user_type', None)
        if user_type == User.THERAPIST:
            self.fields['therapy_license'] = serializers.CharField(
                max_length=255)
            self.fields['specialization'] = serializers.CharField(
                max_length=100)
            self.fields['transaction_id'] = serializers.CharField(
                max_length=100)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('user_type') == User.THERAPIST:
            data.pop('password')
        else:
            # Remove password field for therapists from representation
            data.pop('password')
        return data


class BookingSessionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all(), required=False)
    # user = UserSerializer(read_only=True)

    class Meta:
        model = BookingSession
        fields = ['id', 'user', 'session_date', 'session_time', 'status']
        read_only_fields = ['status']

    def validate(self, data):
        request = self.context.get("request", None)
        session_date = data.get('session_date')
        session_time = data.get('session_time')
        session_datetime = datetime.datetime.combine(
            session_date, session_time)
        session_datetime_naive = datetime.datetime.combine(
            session_date, session_time)

        # Make the datetime object aware by adding timezone information
        session_datetime = make_aware(session_datetime_naive)
 # Combine date and time
        if session_datetime < timezone.now():
            raise serializers.ValidationError(
                "Session datetime cannot be in the past.")
        if session_datetime < timezone.now() + timezone.timedelta(hours=2):
            raise serializers.ValidationError(
                "Session datetime must be at least 2 hours from now.")
        if request is None:
            raise serializers.ValidationError("Request object is invalid.")
        user = request.user
        # Check if the user is a client
        if user.user_type != "client":
            raise serializers.ValidationError(
                "Only clients can book sessions.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        booking_session = BookingSession.objects.create(**validated_data)
        client_email = user.email
        # Assuming phone_number is stored in the User model
        client_phone_number = '254745897362'
        # if client_phone_number:
        #     message = f"Hello {user.first_name}, your booking is confirmed for {booking_session.session_date} at {booking_session.session_time}."
        #     self.send_whatsapp_message(client_phone_number, message)

        # # Send WhatsApp message to the therapist
        # # Replace with actual therapist phone number
        # therapist_phone_number = '254745897362'
        # if therapist_phone_number:
        #     message = f"Hello, you have a new appointment with {user.first_name} on {booking_session.session_date} at {booking_session.session_time}."
        #     self.send_whatsapp_message(therapist_phone_number, message)

        # # Create Google Meet event
        # session_date = validated_data['session_date']
        # session_time = validated_data['session_time']
        # start_datetime = datetime.datetime.combine(session_date, session_time)
        # end_datetime = start_datetime + \
        #     datetime.timedelta(minutes=90)  # 1 hour and 30 minutes

        # # event = create_google_meet_event(
        # #     summary='Booking Session',
        # #     start_time=start_datetime.isoformat(),
        # #     end_time=end_datetime.isoformat(),
        # #     attendees=[client_email]
        # # )

        # Send email to the client
        subject = 'Booking Confirmation'
        message = f'Hello, your booking has been confirmed. Here is your Google Meet link: '
        send_mail(subject, message,
                  settings.DEFAULT_FROM_EMAIL, ['emekadaves10@gmail.com'])

        return booking_session

    # def send_whatsapp_message(self, phone_number, message):
    #     try:
    #         pywhatkit.sendwhatmsg_instantly(f"+{'254795083960'}", message)
    #     except Exception as e:
    #         print(f"An error occurred: {e}")

    def update(self, instance, validated_data):
        user = validated_data.pop("user", None)
        booking_session = super().update(instance, validated_data)
        booking_session.save()
        if user is not None:
            instance.user = user
        instance.save()
        return instance


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'customer_account_number', 'transaction_amount',  'transaction_currency',
                  'transaction_identifier', 'transaction_code', 'transaction_status', 'utilised',
                  ]
        read_only_fields = [
            'transaction_code', 'transaction_identifier', ' transaction_status', 'utilised', 'user']

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request", None)
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")

        user = request.user

        customer_account_number = validated_data.pop("customer_account_number")

        transaction_amount = validated_data.pop("transaction_amount")

        json_data = {
            "customer_account_number": customer_account_number,
            "amount": transaction_amount,
            "receiving_account_number": os.environ.get('FASTDUKA_PAYBILL'),
            "receiving_organization_id": os.environ.get('FASTDUKA_ORGID'),
            "payment_method_name": "mpesa",
            "payment_method_subtype": "stk_push",
            "config_id": os.environ.get('FASTDUKA_CONFIG_ID'),
            "transaction_note": "OpenUp transaction",
        }
        api_key = "Api-Key" + os.environ.get('FASTDUKA_API_KEY')
        api_key = os.environ.get("api_key")
        header = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.fastduka.co.ke/api/transaction/",
            json=json_data,
            headers=header,
        )

        # Check the status code to see if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            # From the response get the idempontent key, Use this key to fetch the transaction and confirm its paid
            paymentTransaction = Transaction.objects.create(
                customer_account_number=customer_account_number,
                transaction_amount=transaction_amount, **validated_data
            )
            # print(response_data)
            paymentTransaction.transaction_identifier = response_data["idempotency_key"]
            paymentTransaction.save()

        else:
            raise serializers.ValidationError(f"{response.text}")

        return paymentTransaction


@transaction.atomic
class ConfirmPaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

    def confirm_payment_status(self):
        payment_transaction = self.instance

        api_key = os.getenv('FASTDUKA_API_KEY')
        header = {
            "Authorization": f"{api_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"https://api.fastduka.co.ke/api/retrieve_transaction_by_idempotency_key/{payment_transaction.transaction_identifier}/",
            headers=header,
        )

        if response.status_code != 200:
            raise serializers.ValidationError(f"{response.text}")
        else:
            response_data = response.json()
            # print(response_data)

            transaction_code = response_data.get(
                "transaction_confirmation_number")
            transaction_status = response_data.get("transaction_status")

            payment_transaction.transaction_code = (
                transaction_code if transaction_code != "" else None)
            payment_transaction.transaction_status = transaction_status
            payment_transaction.save()

        if (
            payment_transaction.transaction_type == "session_booking"
            and payment_transaction.transaction_status == "successful"
        ):

            booked_session = BookingSession.objects.get(
                transaction_id=payment_transaction.id
            )

            booked_session.paid = True
            booked_session.save()

        if (
            payment_transaction.transaction_type == "therapist_subscription"
            and payment_transaction.transaction_status == "successful"
        ):
            # Get the subscription
            therapist_subscription = User.objects.filter(
                transaction__id=transaction.id
            )

            therapist_subscription.paid = True
            therapist_subscription.save()
        if (
            payment_transaction.transaction_type == "donation"
            and payment_transaction.transaction_status == "successful" and payment_transaction.utilised == True

        ):
            # Get the subscription
            donation = Transaction.objects.filter(
                transaction__id=transaction.id
            )

            donation.utilised = True
            donation.save()
        return payment_transaction


class GameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        fields = ['id', 'user', 'player_choice', 'computer_choice',
                  'play_again', 'result', 'created_at']
        read_only_fields = ['created_at', 'user', 'result', 'computer_choice']

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")

        user = request.user
        game = object.create(**validated_data)
        return game


class ChatCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatCompletion
        fields = ['id', 'user_input', 'method',
                  'path', 'user_agent', 'chat_response']


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = [
            'id',
            'link',
            'attendees',
            'reminders',
            'start_time',
            'end_time',
            'created_at'
        ]
