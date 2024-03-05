from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import ( User,  BookingSession,  Transaction, Game, ChatCompletion, Notification)

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Other Fields",
            {
                "fields": (
                    "phone_code",
                    "phone_number",
                    
                   
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
                    "email",
                   

                )
            },
        ),
    )
admin.site.register(User, CustomUserAdmin)
admin.site.register(BookingSession)
admin.site.register(Transaction)
admin.site.register(Game)
admin.site.register(ChatCompletion)
admin.site.register(Notification)

# Register your models here.
