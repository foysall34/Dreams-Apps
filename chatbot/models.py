

from django.db import models
from django.conf import settings

class Dream(models.Model):
    STATUS_CHOICES = [
        ('initial', 'Initial Interpretation Pending'),
        ('answered', 'Ultimate Interpretation Pending'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    interpretation = models.TextField(blank=True, null=True)
    questions = models.JSONField(blank=True, null=True)
    answers = models.JSONField(blank=True, null=True) 
    ultimate_interpretation = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='initial')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        unique_together = ('user', 'text')

    def __str__(self):
        return f"Dream by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
    

class Subscription(models.Model):
    USER_PLAN_CHOICES = [
        ('free', 'free'),
        ('premium', 'premium'), 
        ('platinum', 'platinum'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=10, choices=USER_PLAN_CHOICES, default='free') 
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"