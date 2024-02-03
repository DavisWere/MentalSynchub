from django.shortcuts import render
import calendar

from django.utils import timezone
import requests
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt 
from .openai_utils import generate_chat_completion
from django.db import transaction
import os
from rest_framework import generics
from django.conf import settings
from rest_framework.response import Response
from django.views import View
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import( User, ChatCompletion)
from core.serializers import ( CustomTokenObtainPairSerializer,ChatCompletionSerializer)

class CustomObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer



"""class ChatCompletion(View):
    queryset= ChatCompletion.objects.all()
    serializer_class = ChatCompletionSerializer"""
def chat_completion(request):
    user_input = request.GET.get('user_input', '')
    
    if user_input:
        # Extract relevant information from the request
        request_info = {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            # Include any other relevant information you need
        }

        # Call the OpenAI-related functionality with user input and request info
        chat_response = generate_chat_completion(user_input, request_info)

        # Save the data to the database
        chat_completion_obj = ChatCompletion.objects.create(
            user_input=user_input,
            method=request_info['method'],
            path=request_info['path'],
            user_agent=request_info['user_agent'],
            chat_response=chat_response,
        )

        # Serialize the model instance
        serializer = ChatCompletionSerializer(chat_completion_obj)

        return JsonResponse(serializer.data)
    else:
        return JsonResponse({"error": "Invalid input"})