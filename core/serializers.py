import os
import datetime 
from datetime import timedelta
from django.utils.timezone import make_aware
import requests
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from core.models import ( User,  BookingSession,  Transaction, Game, ChatCompletion)

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
                   'phone_number','nationality', 'avatar', 'therapy_license', 
                     'specialization', 'license_number', 'username','password',
                  ]
        
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     user_type = self.context['request'].data.get('user_type', None)  # Assuming user_type is passed in request data
    #     if user_type == User.THERAPIST:
    #         self.fields['therapy_license'] = serializers.CharField(max_length=255)
    #         self.fields['specialization'] = serializers.CharField(max_length=100)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('user_type') == User.THERAPIST:
            data.pop('password')  # Remove password field for therapists from representation
        return data


class BookingSessionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all(), required=False)
    # user = UserSerializer(read_only=True)
    

    class Meta:
        model =BookingSession
        fields = ['id', 'user', 'session_date', 'session_time', 'status']
        read_only_fields = ['status']

    def validate(self, data):
        request = self.context.get("request", None)
        session_date = data.get('session_date')
        session_time = data.get('session_time')
        session_datetime = datetime.datetime.combine(session_date, session_time) 
        session_datetime_naive = datetime.datetime.combine(session_date, session_time)
        
        # Make the datetime object aware by adding timezone information
        session_datetime = make_aware(session_datetime_naive)
 # Combine date and time
        if session_datetime < timezone.now():
            raise serializers.ValidationError("Session datetime cannot be in the past.")
        if session_datetime < timezone.now() + timezone.timedelta(hours=2):
            raise serializers.ValidationError("Session datetime must be at least 2 hours from now.")
        if request is None:
            raise serializers.ValidationError("Request object is invalid.")
        user = request.user
        # Check if the user is a client
        if user.user_type != "client":
            raise serializers.ValidationError("Only clients can book sessions.")
        return data

        
    
    def create(self, validated_data):
        user = self.context['request'].user
        booking_session = BookingSession.objects.create(**validated_data)
        return booking_session

    def update(self, instance, validated_data):
        user = validated_data.pop("user", None)
        booking_session =super().update(instance, validated_data)
        booking_session.save()
        if user is not None:
            instance.user =user
        instance.save()
        return booking_session

class TransactionSerializer(serializers.ModelSerializer):
    booking_session_id = serializers.PrimaryKeyRelatedField(queryset=BookingSession.objects.all(), 
                                                            write_only=True, required = False)
    

    class Meta:
        model = Transaction
        fields = ['id', 'booking_session_id', 'customer_account_number', 'transaction_amount',  'transaction_currency',
                  'transaction_identifier', 'transaction_code', 'transaction_status','utilised'
                  ]
        read_only_fields = ['transaction_code','transaction_identifier',' transaction_status','utilised']

    # def create(self, validated_data):
    #     booking_session = validated_data.pop('booking_session_id', None)
    #     transaction = Transaction.objects.create(**validated_data)
    #     if booking_session is not None:
    #         transaction.booking_session = booking_session
    #         transaction.save()
    #     return transaction
    
    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request", None)
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")
        
        user = request.user
        booking_session= validated_data.pop("booking_session_id")
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
            # From the response get the idempontent key, Use this key to fetch the transactiona and confirm its paid
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


class GameSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Game
        fields = ['id', 'user', 'player_choice','computer_choice', 'play_again','result', 'created_at']
        read_only_fields = ['created_at', 'user', 'result', 'computer_choice']
        
    def create(self, validated_data):
        request = self.context.get("request", None)
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")

        user = request.user
        game =object.create(**validated_data)
        return game

class ChatCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatCompletion
        fields = ['id','user_input', 'method', 'path', 'user_agent', 'chat_response']
        
