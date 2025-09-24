from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('platinum', 'Platinum'),
    )
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=4, null=True, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='free')


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

   