

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
    



# your_app_name/models.py
from django.db import models

class Feature(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Type your feature")

    def __str__(self):
        return self.name

class Pricing(models.Model):
 
    user_plan = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=1500)
    price = models.FloatField()
    features = models.ManyToManyField(Feature, through='PlanFeature', related_name='plans')

    def __str__(self):
        return f"{self.user_plan}"

    def get_features(self):
     
        feature_list = []

        plan_features = self.planfeature_set.all().select_related('feature')

        for pf in plan_features:
            feature_list.append({
                'name': pf.feature.name,
                'enabled': pf.enabled
            })
        return feature_list

class PlanFeature(models.Model):
  
    pricing_plan = models.ForeignKey(Pricing, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True, help_text="enable or not")

    class Meta:

        unique_together = ('pricing_plan', 'feature')

    def __str__(self):
        return f"{self.pricing_plan.user_plan} - {self.feature.name} ({'Enabled' if self.enabled else 'Disabled'})"