

from django.contrib import admin

from .models import Dream ,Subscription , Pricing,PlanFeature , Feature

class Subcriptions(admin.ModelAdmin):
    list_display = ('id' , 'user'  , 'plan' , 'is_active')

admin.site.register(Subscription , Subcriptions)
admin.site.register(Dream)
admin.site.register(Pricing)
admin.site.register(PlanFeature)
admin.site.register(Feature)