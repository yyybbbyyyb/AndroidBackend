from django.urls import path
from .views import normal_chat, bill_chat, analyze_ledger

urlpatterns = [
    path('normal-chat/', normal_chat, name='normal_chat'),

    path('bill-chat/', bill_chat, name='bill_chat'),

    path('analyze_ledger/', analyze_ledger, name='bill_chat'),
]
