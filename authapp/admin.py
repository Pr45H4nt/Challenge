from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser , Profile
# Register your models here.

# class CustomUserSite(UserAdmin):
#     add_form = CustomUserCreationForm
#     model = CustomUser
#     form = CustomUserCreationForm
#     list_display = [
#         'email', 'username', 'age'
#     ]

#     fieldsets = UserAdmin.fieldsets + (('additional info', {'fields':('age',)}),)
#     add_fieldset = UserAdmin.add_fieldsets + (('additional info', {'fields':('age',)}),)

class C_UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'age', 'profile__bio', 'date_joined' ]

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'user__age']


admin.site.register(CustomUser, C_UserAdmin)
admin.site.register(Profile, ProfileAdmin)
