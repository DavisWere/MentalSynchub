from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import (User)

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


# Register your models here.
