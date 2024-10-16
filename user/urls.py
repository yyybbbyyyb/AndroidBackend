from django.urls import path
from .views import register, user_info, CustomTokenObtainPairView, CustomTokenRefreshView, token_check, LogoutView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # 用户登录
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),  # 刷新Token
    path('token/check/', token_check, name='token_check'),  # Token
    path('register/', register, name='register'),  # 用户注册
    path('user/', user_info, name='get_user_info'),  # 获取用户信息
    path('logout/', LogoutView.as_view(), name='logout'),  # 用户登出
]
