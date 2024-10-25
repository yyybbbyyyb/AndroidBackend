from rest_framework.routers import DefaultRouter

from . import views
from django.urls import path


urlpatterns = [
    path("monthly-report/", views.monthly_report, name="monthly_report"),
    path("daily-report/", views.daily_report, name="daily_report"),

    path('ledgers/', views.ledger_list, name='ledger-list'),  # 获取所有账本/创建账本
    path('ledgers/<int:pk>/', views.ledger_detail, name='ledger-detail'),  # 获取/更新/删除单个账本
    path('bills/', views.bill_list, name='bill-list'),  # For GET and POST (list all, create new)
    path('bills/<int:pk>/', views.bill_detail, name='bill-detail'),  # For GET, PUT, DELETE (retrieve, update, delete)
    path('budgets/', views.budget_list, name='budget-list'),  # For GET and POST (list all, create new)
    path('budgets/<int:pk>/', views.budget_detail, name='budget-detail'),  # For GET, PUT, DELETE (retrieve, update, delete)

    path('total-expense-by-category/', views.total_expense_by_category, name='category-list'),
    path('total-budget/', views.total_budget, name='month-list'),
]

