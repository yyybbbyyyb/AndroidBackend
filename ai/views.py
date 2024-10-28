from rest_framework import status
from django.conf import settings
from django.utils.timezone import datetime

from .openai_client import OpenAIClient
from utils.utils import success_response, fail_response
from rest_framework.decorators import api_view
from .prompt import generate_bill_prompt, generate_analysis_prompt
import json
from bill.models import Ledger, Category, Bill
from django.db import models
from decimal import Decimal

# 配置API密钥和地址
API_KEY = settings.OPENAI_API_KEY  # 替换为你的OpenAI API密钥
BASE_URL = settings.OPENAI_BASE_URL  # 替换为你的OpenAI API地址

# 初始化OpenAI客户端
ai_client = OpenAIClient(api_key=API_KEY, base_url=BASE_URL)


@api_view(['POST'])
def normal_chat(request):
    try:
        user_message = request.data.get('message')

        if not user_message:
            return fail_response(message="未提供消息内容", status_code=status.HTTP_400_BAD_REQUEST)

        # prompt = generate_bill_prompt(user_message)

        prompt = user_message + "请不要超过100字"

        ai_response = ai_client.get_chat_response(prompt)

        return success_response(data={
            "response": ai_response,
            "ai_avatar": "0"
        }, message="成功获取AI回复")

    except Exception as e:
        return fail_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bill_chat(request):
    try:
        user_message = request.data.get('message')
        ledger_id = request.data.get('ledger_id')

        if not user_message:
            return fail_response(message="未提供消息内容", status_code=status.HTTP_400_BAD_REQUEST)
        if not ledger_id:
            return fail_response(message="未提供账本ID", status_code=status.HTTP_400_BAD_REQUEST)

        # 生成prompt
        prompt = generate_bill_prompt(user_message)

        # 调用OpenAI API获取回复
        ai_response = ai_client.get_chat_response(prompt)

        # 检查AI响应是否为空
        if not ai_response:
            return fail_response(message="AI未返回任何响应", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 解析AI的响应，期望返回JSON格式
        response_data = None
        try:
            # 尝试解析为 JSON 格式
            response_data = json.loads(ai_response)
        except json.JSONDecodeError:
            # 如果解析失败，检查是否是字符串格式的 JSON
            if isinstance(ai_response, str):
                # 如果包含代码块格式（例如 ```json ... ```），去掉这些字符
                ai_response = ai_response.strip().strip("```").strip("json").strip()
                try:
                    response_data = json.loads(ai_response)
                except json.JSONDecodeError:
                    return fail_response(message="AI响应的格式不正确",
                                         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 校验响应数据的字段
        required_fields = {"inOutType", "detail_type", "amount", "remark", "response", "emoji"}
        if not all(field in response_data for field in required_fields):
            return fail_response(message="AI响应缺少必要的字段", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 检查账本是否存在，并且用户有权限访问
        try:
            ledger = Ledger.objects.get(id=ledger_id, user=request.user)
        except Ledger.DoesNotExist:
            return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)

        # 下面这些其实可以用序列化器，但我bill增删改查的接口和现在的数据形式有点不匹配，只能这样写了
        category_data = {
            'inOutType': response_data['inOutType'],
            'detail_type': response_data['detail_type']
        }
        category, created = Category.objects.get_or_create(
            inOutType=category_data['inOutType'],
            detail_type=category_data['detail_type']
        )

        # 手动创建Bill对象
        bill = Bill.objects.create(
            ledger=ledger,
            category=category,
            amount=response_data['amount'],
            remark=response_data['remark'],
            date=request.data.get('date', datetime.now().strftime('%Y-%m-%d'))  # 如果未提供日期，使用当前日期
        )

        # 准备返回的数据
        return_data = {
            'response': response_data.get('response'),
            'ai_avatar': response_data.get('emoji'),
            'bill': {
                'id': bill.id,
                'ledger': bill.ledger.id,
                'amount': bill.amount,
                'remark': bill.remark,
                'date': bill.date,
                'create_time': bill.create_time
            }
        }

        return success_response(data=return_data, message="创建账单成功", status_code=status.HTTP_201_CREATED)


    except Exception as e:
        # 捕获异常，返回自定义错误响应
        return fail_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def analyze_ledger(request):
    try:
        ledger_id = request.query_params.get('ledger_id')

        if not ledger_id:
            return fail_response(message="未提供账本ID", status_code=status.HTTP_400_BAD_REQUEST)

        # 检查账本是否存在，并且用户有权限访问
        try:
            ledger = Ledger.objects.get(id=ledger_id, user=request.user)
        except Ledger.DoesNotExist:
            return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)

        # 获取当前日期
        current_date = datetime.now()

        # 获取这个月的所有收入和支出
        income = Bill.objects.filter(
            ledger=ledger,
            category__inOutType='1',  # 收入
            date__year=current_date.year,
            date__month=current_date.month
        ).aggregate(total_income=models.Sum('amount'))['total_income'] or Decimal('0')

        expense = Bill.objects.filter(
            ledger=ledger,
            category__inOutType='2',  # 支出
            date__year=current_date.year,
            date__month=current_date.month
        ).aggregate(total_expense=models.Sum('amount'))['total_expense'] or Decimal('0')

        # 获取各类别支出详情
        category_expenses = Bill.objects.filter(
            ledger=ledger,
            category__inOutType='2',  # 支出
            date__year=current_date.year,
            date__month=current_date.month
        ).values('category__detail_type').annotate(total=models.Sum('amount')).order_by('-total')

        # 生成类别支出摘要
        category_summary = "\n".join([
            f"{Category.objects.filter(detail_type=cat['category__detail_type'], inOutType='2').first().get_detail_type_display()}：{cat['total']}元"
            for cat in category_expenses
        ])

        # 检查支出是否超过收入的80%
        is_warning = expense > (income * Decimal('0.7'))

        if is_warning:
            prompt = generate_analysis_prompt(income, expense, category_summary)
            ai_response = ai_client.get_chat_response(prompt)
            ai_response = "本月支出较多，" + ai_response
        else:
            ai_response = "本月支出正常，继续保持！"

        # 检查AI响应是否为空
        if not ai_response:
            return fail_response(message="AI未返回任何响应", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 准备返回的数据
        return_data = {
            'response': ai_response,
            'is_warning': is_warning
        }

        return success_response(data=return_data, message="分析完成", status_code=status.HTTP_200_OK)

    except Exception as e:
        # 捕获异常，返回自定义错误响应
        return fail_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

