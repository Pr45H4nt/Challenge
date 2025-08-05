from django.urls import path
from .views import UserAPI, ProfileAPI, RoomAPI, SessionAPI, TodoAPI, TrackTodoAPI
from .views import NoticeAPI
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'profile', ProfileAPI)
router.register(r'room',RoomAPI )
router.register(r'session', SessionAPI)
router.register(r'todo', TodoAPI)
router.register(r'tracktodo', TrackTodoAPI)
router.register(r'notice', NoticeAPI)

urlpatterns = [
    path('user/', UserAPI.as_view(), name='user-api'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('profile/', ProfileAPI.as_view(), name='profile-api'),
] + router.urls