from lib2to3.fixes.fix_input import context

from rest_framework import serializers
from .models import User
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'gender', 'avatar', 'phone', 'email']
        read_only_fields = ['id', 'username']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.avatar:
            avatar_url = self.context['request'].build_absolute_uri(instance.avatar.url)
        else:
            if instance.gender == 'M':
                avatar_url = self.context['request'].build_absolute_uri('/static/avatar/default_ava_mail.png')
            else:
                avatar_url = self.context['request'].build_absolute_uri('/static/avatar/default_ava_femail.png')
        representation['avatar'] = avatar_url

        # 计算用户使用天数
        representation['used_days'] = (timezone.now() - instance.date_joined).days

        return representation

    def validate(self, data):
        cur_pwd = self.context['request'].data.get('current_password', None)
        new_pwd = self.context['request'].data.get('new_password', None)

        if new_pwd:
            if not cur_pwd:
                raise serializers.ValidationError({'current_password': '请输入当前密码'})

            if not self.instance.check_password(cur_pwd):
                raise serializers.ValidationError({'current_password': '当前密码错误'})
        return data

    def update(self, instance, validated_data):
        new_pwd = self.context['request'].data.get('new_password', None)

        if new_pwd:
            instance.set_password(new_pwd)

        return super().update(instance, validated_data)



class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)