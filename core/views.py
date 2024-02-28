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
from django.db import transaction
import os
from rest_framework import generics
from django.conf import settings
from rest_framework.response import Response
from django.views import View
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import( User, ChatCompletion)
from core.serializers import ( CustomTokenObtainPairSerializer,ChatCompletionSerializer, UserSerializer)

class CustomObtainTokenPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset= User.objects.all()
    permission_classes = [permissions.IsAuthenticated]



class ChatCompletion(View):
    queryset= ChatCompletion.objects.all()
    serializer_class = ChatCompletionSerializer
