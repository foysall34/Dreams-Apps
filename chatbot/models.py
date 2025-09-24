# dreams/models.py

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
    questions = models.JSONField(blank=True, null=True) # Use JSONField for list of questions
    answers = models.JSONField(blank=True, null=True) # Use JSONField for list of answers
    ultimate_interpretation = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='initial')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A user can only have one active interpretation cycle per dream text
        unique_together = ('user', 'text')

    def __str__(self):
        return f"Dream by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"