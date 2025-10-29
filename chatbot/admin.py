

from django.contrib import admin
from django.utils import timezone
from .models import Dream ,Subscription , Pricing,PlanFeature , Feature

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'updated_at')
    readonly_fields = ('stripe_customer_id', 'stripe_subscription_id')

    def save_model(self, request, obj, form, change):
        obj.updated_at = timezone.now()
        super().save_model(request, obj, form, change)






admin.site.register(Dream)
# admin.site.register(Pricing)
admin.site.register(PlanFeature)
admin.site.register(Feature)

class Pricingss(admin.ModelAdmin):
    list_display = ('id' , 'plan_type' , 'billing_interval')
admin.site.register(Pricing, Pricingss )