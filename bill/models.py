from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from user.models import User

class Ledger(models.Model):
    name = models.CharField(max_length=255, verbose_name='账本名称')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')  # 假设你有用户系统
    image = models.CharField(max_length=2, verbose_name='账本封面', blank=True, default='0')
    isDefault = models.BooleanField(default=False, verbose_name='是否默认账本')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name

class Category(models.Model):
    INCOME = '1'
    EXPENSE = '2'
    INOUT_TYPE_CHOICES = [
        (INCOME, '收入'),
        (EXPENSE, '支出'),
    ]

    inOutType = models.CharField(max_length=1, choices=INOUT_TYPE_CHOICES, verbose_name='收支类型', default=EXPENSE)

    DETAIL_TYPE_INCOME = [
        ('1', '工资'), ('2', '生活费'), ('3', '奖金'), ('4', '理财'),
        ('5', '收红包'), ('6', '外快'), ('7', '零花钱'), ('8', '其他'),
    ]

    DETAIL_TYPE_EXPENSE = [
        ('1', '餐饮'), ('2', '交通'), ('3', '日用品'), ('4', '购物'),
        ('5', '零食'), ('6', '饮品'), ('7', '蔬菜'), ('8', '水果'),
        ('9', '服饰'), ('10', '娱乐'), ('11', '美容'), ('12', '通讯'),
        ('13', '医疗'), ('14', '学习'), ('15', '游戏'), ('16', '红包'),
        ('17', '婴儿用品'), ('18', '酒店'), ('19', '住房'), ('20', '转账'),
        ('21', '社交'), ('22', '礼品'), ('23', '宠物'), ('24', '汽车'),
        ('25', '数码'), ('26', '书籍'), ('27', '追星'), ('28', '办公'),
        ('29', '运动'), ('30', '捐赠'), ('31', '金融'), ('32', '其他'),
    ]

    detail_type = models.CharField(max_length=2, verbose_name='详细类型')

    def get_detail_type_display(self):
        """根据 inOutType 和 detail_type 返回详细类型的显示名称"""
        if self.inOutType == self.INCOME:
            detail_type_dict = dict(self.DETAIL_TYPE_INCOME)
        elif self.inOutType == self.EXPENSE:
            detail_type_dict = dict(self.DETAIL_TYPE_EXPENSE)
        else:
            return "未知类型"
        return detail_type_dict.get(self.detail_type, "未知类型")

    def clean(self):
        """根据 inOutType 验证 detail_type 的合法性"""
        if self.inOutType == self.INCOME and self.detail_type not in dict(self.DETAIL_TYPE_INCOME):
            raise ValidationError('收入类型下的详细类型选择不合法。')
        if self.inOutType == self.EXPENSE and self.detail_type not in dict(self.DETAIL_TYPE_EXPENSE):
            raise ValidationError('支出类型下的详细类型选择不合法。')

    class Meta:
        unique_together = ('inOutType', 'detail_type')

    def __str__(self):
        return f"{self.get_inOutType_display()}"

class Bill(models.Model):
    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE, verbose_name='账本')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='类别')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    remark = models.CharField(max_length=255, verbose_name='备注', blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='记录日期')
    date = models.DateField(verbose_name='账单日期')

    def __str__(self):
        return f"{self.category} - {self.amount}"

class Budget(models.Model):
    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE, verbose_name='账本')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='类别')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='预算金额')
    month = models.PositiveIntegerField(verbose_name='月份')  # 1-12
    year = models.PositiveIntegerField(verbose_name='年份', default=timezone.now().year)  # 预算对应的年份

    def __str__(self):
        return f"{self.ledger} - {self.category} - {self.budget_amount} ({self.year}/{self.month})"

    class Meta:
        unique_together = ('ledger', 'category', 'month', 'year')  # 同一账本、类别和月份下的预算应该是唯一的


