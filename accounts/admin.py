from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# UserAdmin থেকে উত্তরাধিকার সূত্রে প্রাপ্ত একটি নতুন অ্যাডমিন ক্লাস তৈরি করুন
class CustomUserAdmin(UserAdmin):
    # অ্যাডমিন লিস্ট ভিউতে কোন কোন ফিল্ড দেখানো হবে তা নির্ধারণ করুন
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    
    # কোন ফিল্ডের উপর ভিত্তি করে ফিল্টার করা যাবে তা নির্ধারণ করুন
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    # কোন ফিল্ডে সার্চ করা যাবে তা নির্ধারণ করুন
    search_fields = ('email', 'first_name', 'last_name')
    
    # ডিফল্টভাবে কিসের উপর ভিত্তি করে সাজানো হবে তা নির্ধারণ করুন
    ordering = ('email',)

    # ইউজার এডিট করার সময় ফর্মটি কেমন হবে তা কাস্টমাইজ করুন
    # যেহেতু আমরা username এর পরিবর্তে email ব্যবহার করছি, তাই fieldsets কাস্টমাইজ করা ভালো
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # নতুন ইউজার তৈরি করার সময় ফর্মটি কেমন হবে
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'password2'),
        }),
    )

# আপনার কাস্টম User মডেল এবং কাস্টম অ্যাডমিন ক্লাস রেজিস্টার করুন
admin.site.register(User, CustomUserAdmin)