from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="操作成功", status_code=status.HTTP_200_OK):
    return Response({
        "status": "success",
        "message": message,
        "data": data
    }, status=status_code)

def fail_response(errors=None, message="操作失败", status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        "status": "error",
        "message": message,
        "errors": errors
    }, status=status_code)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return fail_response(
            message="服务器内部错误",
            errors=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data = {
            "status": "error",
            "message": "身份认证失败，请提供有效的认证信息。",
            "errors": response.data
        }
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        response.data = {
            "status": "error",
            "message": "请求参数无效。",
            "errors": response.data
        }
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        response.data = {
            "status": "error",
            "message": "权限不足。",
            "errors": response.data
        }
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = {
            "status": "error",
            "message": "资源未找到。",
            "errors": response.data
        }
    else:
        response.data = {
            "status": "error",
            "message": "未知错误，请联系管理员。",
            "errors": response.data
        }

    return response
