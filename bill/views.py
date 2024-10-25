from calendar import month

import django_filters

from .models import Bill, Ledger, Budget, Category
from .serializers import BillSerializer, LedgerSerializer, BudgetSerializer
from django.db.models import Sum
from rest_framework import status
from decimal import Decimal
from rest_framework.decorators import api_view

from utils.utils import success_response, fail_response


@api_view(['GET', 'POST'])
def ledger_list(request):
    if request.method == 'GET':
        # 获取当前用户所有账本
        ledgers = Ledger.objects.filter(user=request.user)
        serializer = LedgerSerializer(ledgers, many=True)
        return success_response(data=serializer.data, message="获取账本列表成功")

    elif request.method == 'POST':
        # 创建新账本
        serializer = LedgerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return success_response(data=serializer.data, message="创建账本成功", status_code=status.HTTP_201_CREATED)
        return fail_response(errors=serializer.errors, message="创建账本失败", status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def ledger_detail(request, pk):
    try:
        # 查找账本
        ledger = Ledger.objects.get(pk=pk, user=request.user)
    except Ledger.DoesNotExist:
        return fail_response(message="未找到该账本", status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # 获取单个账本信息
        serializer = LedgerSerializer(ledger)
        return success_response(data=serializer.data, message="获取账本信息成功")

    elif request.method == 'PUT':
        # 更新账本信息
        serializer = LedgerSerializer(ledger, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="账本更新成功")
        return fail_response(errors=serializer.errors, message="更新账本失败", status_code=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if ledger.isDefault:
            return fail_response(message="无法删除默认账本", status_code=status.HTTP_400_BAD_REQUEST)
        ledger.delete()
        return success_response(message="账本删除成功")


class BillFilter(django_filters.FilterSet):
    # 按日期范围过滤
    date = django_filters.DateFromToRangeFilter(field_name='date')

    # 自定义过滤器：按年、月、日过滤
    year = django_filters.NumberFilter(field_name='date__year')
    month = django_filters.NumberFilter(field_name='date__month')
    day = django_filters.NumberFilter(field_name='date__day')

    # 按类别的inOutType和detail_type字段进行过滤
    inOutType = django_filters.CharFilter(field_name='category__inOutType')
    detail_type = django_filters.CharFilter(field_name='category__detail_type')

    class Meta:
        model = Bill
        fields = ['inOutType', 'detail_type', 'date', 'year', 'month', 'day']


@api_view(['GET', 'POST'])
def bill_list(request):
    if request.method == 'GET':
        ledger_id = request.query_params.get('ledger_id')

        bills = Bill.objects.filter(ledger__user=request.user, ledger_id=ledger_id)

        # 过滤
        filterset = BillFilter(request.GET, queryset=bills)
        bills = filterset.qs

        # 排序
        ordering = request.GET.get('ordering')
        if ordering:
            bills = bills.order_by(ordering)

        return success_response(data=BillSerializer(bills, many=True).data, message="获取账单列表成功")

    elif request.method == 'POST':
        serializer = BillSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ledger_id = serializer.validated_data.get('ledger').id
            try:
                ledger = Ledger.objects.get(id=ledger_id, user=request.user)
            except Ledger.DoesNotExist:
                return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return success_response(data=serializer.data, message="创建账单成功", status_code=status.HTTP_201_CREATED)
        return fail_response(errors=serializer.errors, message="创建账单失败", status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def bill_detail(request, pk):
    try:
        bill = Bill.objects.get(pk=pk, ledger__user=request.user)
    except Bill.DoesNotExist:
        return fail_response(message="未找到该账单", status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BillSerializer(bill)
        return success_response(data=serializer.data, message="获取账单信息成功")

    elif request.method == 'PUT':
        serializer = BillSerializer(bill, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            ledger = serializer.validated_data.get('ledger')
            if ledger:
                if ledger.user != request.user:
                    return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return success_response(data=serializer.data, message="更新账单成功")
        return fail_response(errors=serializer.errors, message="更新账单失败", status_code=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        bill.delete()
        return success_response(message="账单删除成功")

class BudgetFilter(django_filters.FilterSet):
    # 自定义过滤器：按年、月过滤
    year = django_filters.NumberFilter(field_name='year')
    month = django_filters.NumberFilter(field_name='month')

    class Meta:
        model = Budget
        fields = ['year', 'month']

@api_view(['GET', 'POST'])
def budget_list(request):
    if request.method == 'GET':
        ledger_id = request.query_params.get('ledger')

        budgets = Budget.objects.filter(ledger__user=request.user, ledger_id=ledger_id)
        serializer = BudgetSerializer(budgets, many=True)
        return success_response(data=serializer.data, message="获取预算列表成功")

    elif request.method == 'POST':
        ledger_id = request.data.get('ledger')
        category_data = request.data.get('category')
        category, _ = Category.objects.get_or_create(
            inOutType=category_data['inOutType'],
            detail_type=category_data['detail_type']
        )
        month = request.data.get('month')
        year = request.data.get('year')

        if category is not None:
            existing_budgets = Budget.objects.filter(
                ledger_id=ledger_id,
                category=category,
                month=month,
                year=year
            )
            if existing_budgets.exists():
                return fail_response(message="该类别的预算本月已存在", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = BudgetSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ledger_id = serializer.validated_data.get('ledger').id
            try:
                ledger = Ledger.objects.get(id=ledger_id, user=request.user)
            except Ledger.DoesNotExist:
                return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return success_response(data=serializer.data, message="创建预算成功", status_code=status.HTTP_201_CREATED)
        return fail_response(errors=serializer.errors, message="创建预算失败", status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def budget_detail(request, pk):
    try:
        budget = Budget.objects.get(pk=pk, ledger__user=request.user)
    except Budget.DoesNotExist:
        return fail_response(message="未找到该预算", status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BudgetSerializer(budget)
        return success_response(data=serializer.data, message="获取预算信息成功")

    elif request.method == 'PUT':
        serializer = BudgetSerializer(budget, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            ledger_id = serializer.validated_data.get('ledger').id
            try:
                ledger = Ledger.objects.get(id=ledger_id, user=request.user)
            except Ledger.DoesNotExist:
                return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return success_response(data=serializer.data, message="更新预算成功")
        return fail_response(errors=serializer.errors, message="更新预算失败", status_code=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        budget.delete()
        return success_response(message="预算删除成功")


# ---------------------------------------------------------------------------------------------------------------


@api_view(['GET'])
def monthly_report(request):
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    ledger_id = request.query_params.get('ledger_id')

    if not all([month, year, ledger_id]):
        return fail_response(message="参数不完整", status_code=status.HTTP_400_BAD_REQUEST)

    try:
        ledger = Ledger.objects.get(id=ledger_id, user=request.user)
    except Ledger.DoesNotExist:
        return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)

    # 计算月度收入和支出
    income = Bill.objects.filter(
        category__inOutType='1',  # 收入类型
        date__month=month,
        date__year=year,
        ledger_id=ledger_id,
        ledger__user=request.user
    ).aggregate(total_income=Sum('amount'))['total_income'] or Decimal('0.00')

    expense = Bill.objects.filter(
        category__inOutType='2',  # 支出类型
        date__month=month,
        date__year=year,
        ledger_id=ledger_id,
        ledger__user=request.user
    ).aggregate(total_expense=Sum('amount'))['total_expense'] or Decimal('0.00')

    # 保留两位小数，确保即使是整数形式也显示为两位小数
    income = Decimal(income).quantize(Decimal('0.00'))
    expense = Decimal(expense).quantize(Decimal('0.00'))

    result = {"income": str(income), "expense": str(expense)}

    return success_response(data=result, message="获取月度报表成功。")

@api_view(['GET'])
def daily_report(request):
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    day = request.query_params.get('day')
    ledger_id = request.query_params.get('ledger_id')

    if not all([month, year, day, ledger_id]):
        return fail_response(message="参数不完整", status_code=status.HTTP_400_BAD_REQUEST)

    try:
        ledger = Ledger.objects.get(id=ledger_id, user=request.user)
    except Ledger.DoesNotExist:
        return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_400_BAD_REQUEST)

    # 计算当日收入和支出
    income = Bill.objects.filter(
        category__inOutType='1',  # 收入类型
        date=f"{year}-{month}-{day}",
        ledger_id=ledger_id,
        ledger__user=request.user
    ).aggregate(total_income=Sum('amount'))['total_income'] or Decimal('0.0')

    expense = Bill.objects.filter(
        category__inOutType='2',  # 支出类型
        date=f"{year}-{month}-{day}",
        ledger_id=ledger_id,
        ledger__user=request.user
    ).aggregate(total_expense=Sum('amount'))['total_expense'] or Decimal('0.0')

    # 保留两位小数，确保即使是整数形式也显示为两位小数
    income = Decimal(income).quantize(Decimal('0.0'))
    expense = Decimal(expense).quantize(Decimal('0.0'))

    result = {"income": str(income), "expense": str(expense)}

    return success_response(data=result, message="获取日报表成功。")


@api_view(['GET'])
def total_expense_by_category(request):
    ledger_id = request.query_params.get('ledger_id')
    inOutType = request.query_params.get('inOutType')
    detail_type = request.query_params.get('detail_type')
    month = request.query_params.get('month')
    year = request.query_params.get('year')

    if not all([ledger_id, inOutType, detail_type, month, year]):
        return fail_response(message="参数不完整", status_code=status.HTTP_400_BAD_REQUEST)

    # 验证账本存在并属于当前用户
    try:
        ledger = Ledger.objects.get(id=ledger_id, user=request.user)
    except Ledger.DoesNotExist:
        return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_404_NOT_FOUND)

    # 计算
    total_expense = Bill.objects.filter(
        ledger_id=ledger_id,
        ledger__user=request.user,
        category__inOutType=inOutType,
        category__detail_type=detail_type,
        date__month=month,
        date__year=year
    ).aggregate(total_expense=Sum('amount'))['total_expense'] or Decimal('0.00')

    return success_response(data={"total_expense": str(total_expense)}, message="获取类别总支出成功")

@api_view(['GET'])
def total_budget(request):
    ledger_id = request.query_params.get('ledger_id')
    month = request.query_params.get('month')
    year = request.query_params.get('year')

    if not all([ledger_id, month, year]):
        return fail_response(message="参数不完整", status_code=status.HTTP_400_BAD_REQUEST)

    # 验证账本存在并属于当前用户
    try:
        ledger = Ledger.objects.get(id=ledger_id, user=request.user)
    except Ledger.DoesNotExist:
        return fail_response(message="账本不存在或无权限访问", status_code=status.HTTP_404_NOT_FOUND)

    # 计算
    total_budget = Budget.objects.filter(
        ledger_id=ledger_id,
        ledger__user=request.user,
        month=month,
        year=year
    ).aggregate(total_budget=Sum('amount'))['total_budget'] or Decimal('0.00')

    return success_response(data={"total_budget": str(total_budget)}, message="获取总预算成功")