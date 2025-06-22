# urls.py
from django.urls import path
from .views import create_payment

app_name = 'payment'

urlpatterns = [
    path('create_payment/', create_payment, name='create_payment'),
]
