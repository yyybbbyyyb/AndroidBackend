from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserSerializer, UserRegisterSerializer
from utils.utils import success_response, fail_response

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return success_response(message="用户注册成功", status_code=status.HTTP_201_CREATED)
    return fail_response(errors=serializer.errors, message="用户注册失败", status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
def user_info(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user, context={'request': request})
        return success_response(data=serializer.data)

    else:
        avatar = request.data.get('avatar')
        print(f"Request Data (avatar): {avatar}")  # 确保 avatar 是一个文件对象，而不是字符串
        print(f"Type of avatar: {type(avatar)}")  # 打印 avatar 的类型，应该是 InMemoryUploadedFile 或 TemporaryUploadedFile

        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return success_response(message="用户信息修改成功")
        return fail_response(errors=serializer.errors, message="用户信息修改失败")

