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
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"
    




class Feature(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Pricing(models.Model):
    PLAN_CHOICES = [
        ('free' , 'Free'),
        ('premium', 'Dream Premium'),
        ('platinum', 'Dream Platinum'),
    ]

    BILLING_INTERVAL_CHOICES = [
        ('month', 'Per month'),
        ('year', 'Per year'),
        ('2year', 'Every 2 years'),
    ]
    stripe_price_id = models.CharField(max_length=255, unique=True , null= True , blank= True)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES , default='free')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    billing_interval = models.CharField(max_length=10, choices=BILLING_INTERVAL_CHOICES , default='month')
    interval_count = models.PositiveIntegerField(default=1 )  # months or years
    currency = models.CharField(max_length=10, default="USD")
    description = models.TextField()

    features = models.ManyToManyField('Feature', through='PlanFeature', related_name='pricing_plans')

    def __str__(self):
        return f"{self.get_plan_type_display()} - {self.price} {self.currency} ({self.get_billing_interval_display()})"

    def get_features(self):
        return [
            {'name': pf.feature.name, 'enabled': pf.enabled}
            for pf in self.planfeature_set.select_related('feature')
        ]






class PlanFeature(models.Model):
    pricing_plan = models.ForeignKey(Pricing, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('pricing_plan', 'feature')

    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.pricing_plan} - {self.feature.name} ({status})"