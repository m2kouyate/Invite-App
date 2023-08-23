from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db import models
from datetime import datetime, timedelta


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    invite_code = models.CharField(max_length=6, unique=True, null=True, blank=True)
    used_invite_code = models.ForeignKey('InviteCode', on_delete=models.SET_NULL, null=True, blank=True)

    # Переопределение связей для избежания конфликта
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="customuser_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="customuser_user_permissions",
        related_query_name="user",
    )


class InviteCode(models.Model):
    code = models.CharField(max_length=6, unique=True)
    creator = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='created_invite_code')
    users = models.ManyToManyField(CustomUser, related_name='used_invite_codes')


class AuthCode(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        # Считаем код действительным в течение 10 минут
        return datetime.now() - self.created_at < timedelta(minutes=10)
