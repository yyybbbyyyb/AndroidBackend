from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from .serializers import UserSerializer, UserRegisterSerializer
from utils.utils import success_response, fail_response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
@authentication_classes([])  # 不要求JWT认证
@permission_classes([AllowAny])
def register(request):
    print(11)
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return success_response(message="用户注册成功", status_code=status.HTTP_201_CREATED)
    return fail_response(errors=serializer.errors, message="用户注册失败", status_code=status.HTTP_400_BAD_REQUEST)


# 继承TokenObtainPairView
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # 调用父类方法
        data = response.data

        # 使用自定义的success_response格式返回
        return success_response(data=data, message="登录成功", status_code=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # 调用父类方法
        data = response.data

        # 使用自定义的success_response格式返回
        return success_response(data=data, message="Token刷新成功", status_code=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="用户登出成功", status_code=status.HTTP_200_OK)
        except Exception as e:
            return fail_response(errors=str(e), message="用户登出失败", status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def token_check(request):
    return success_response(message="Token有效", status_code=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def user_info(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user, context={'request': request})
        return success_response(data=serializer.data)

    else:
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return success_response(message="用户信息修改成功")
        return fail_response(errors=serializer.errors, message="用户信息修改失败")
