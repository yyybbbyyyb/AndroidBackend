from django.db.models.signals import post_save
from django.dispatch import receiver
from user.models import User
from .models import Ledger

# 每次用户注册时自动创建一个默认账本
@receiver(post_save, sender=User)
def create_default_ledger(sender, instance, created, **kwargs):
    if created:
        Ledger.objects.create(name="默认账本", user=instance, isDefault=True)