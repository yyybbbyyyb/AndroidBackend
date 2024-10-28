from rest_framework import serializers
from .models import Bill, Ledger, Budget, Category

class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = ['id', 'name', 'create_time', 'image', 'isDefault']  # 移除 user 字段
        read_only_fields = ['id', 'create_time', 'isDefault']  # 设置只读字段

class BillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bill
        fields = ['id', 'ledger', 'amount', 'remark', 'create_time', 'date']
        read_only_fields = ['id', 'create_time']

    def create(self, validated_data):
        category_data = self.context['request'].data.get('category')
        # 获取或创建 Category
        category, created = Category.objects.get_or_create(
            inOutType=category_data['inOutType'],
            detail_type=category_data['detail_type']
        )

        bill = Bill.objects.create(category=category, **validated_data)
        return bill

    def update(self, instance, validated_data):
        # 处理 Category
        category_data = self.context['request'].data.get('category')
        if category_data:
            category, created = Category.objects.get_or_create(
                inOutType=category_data['inOutType'],
                detail_type=category_data['detail_type']
            )
            instance.category = category

        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        # 返回时添加 category 的详细信息
        representation = super().to_representation(instance)
        representation['category'] = {
            'inOutType': instance.category.inOutType,
            'detail_type': instance.category.detail_type
        }

        # 返回时添加 ledger 的详细信息
        representation['ledger_name'] = instance.ledger.name
        return representation

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'ledger', 'amount', 'month', 'year']
        read_only_fields = ['id']

    def create(self, validated_data):
        category_data = self.context['request'].data.get('category')
        # 获取或创建 Category
        category, created = Category.objects.get_or_create(
            inOutType=category_data['inOutType'],
            detail_type=category_data['detail_type']
        )

        budget = Budget.objects.create(category=category, **validated_data)
        return budget

    def update(self, instance, validated_data):
        # 处理 Category
        category_data = self.context['request'].data.get('category')
        if category_data:
            category, created = Category.objects.get_or_create(
                inOutType=category_data['inOutType'],
                detail_type=category_data['detail_type']
            )
            instance.category = category

        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        # 返回时添加 category 的详细信息
        representation = super().to_representation(instance)
        representation['category'] = {
            'inOutType': instance.category.inOutType,
            'detail_type': instance.category.detail_type
        }
        return representation


