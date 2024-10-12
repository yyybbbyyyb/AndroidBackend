from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import register, user_info

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # 用户登录
    path('register/', register, name='register'),  # 用户注册
    path('user/', user_info, name='get_user_info'),  # 获取用户信息
]
