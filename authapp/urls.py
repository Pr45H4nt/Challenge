from django.urls import path
from .views import *
urlpatterns = [
    path('signup/', SignupView.as_view(), name="signup"),
    path('login/', Login.as_view(), name="login"),
    path('logout/', logoutview, name='logout'),
    path('changepass/', passwordchangeview, name='changepass'),
    path('editprofile/', profileview, name='editprofile'),
    path('createprofile/', ProfileCreateView.as_view(), name='createprofile'),
    path('<str:username>/', DisplayProfileView.as_view(), name='profile'),
    path('user/settings/', SettingsView.as_view(), name='settings'),
    path('login/demo/', demoaccountlogin, name='demo-account-login'),
]