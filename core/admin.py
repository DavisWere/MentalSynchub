from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import (User,  BookingSession,
                         Transaction, ChatCompletion, Notification, Schedule)


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Other Fields",
            {
                "fields": (
                    "phone_code",
                    "phone_number",
                    "user_type",
                    'transaction_id',




                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Other Fields",
            {
                "fields": (
                    "phone_code",
                    "phone_number",
                    "user_type",
                    "email",
                    'transaction_id',
                    'password'


                )
            },
        ),
    )


class ScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'start_time',
        'end_time',
        'reminders',
        'link'
    ]


admin.site.register(User, CustomUserAdmin)
admin.site.register(BookingSession)
admin.site.register(Transaction)
admin.site.register(ChatCompletion)
admin.site.register(Notification)
admin.site.register(Schedule, ScheduleAdmin)

# Register your models here.
