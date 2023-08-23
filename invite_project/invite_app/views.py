from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model, login
from rest_framework.authtoken.models import Token
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
import random
import time

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import InviteCode, CustomUser, AuthCode


# Эмуляция отправки кода
@api_view(['POST'])
def send_code(request):
    """Отправка кода"""
    phone_number = request.data.get('phone_number')

    if not phone_number:
        return Response({"detail": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Имитация задержки на сервере
    time.sleep(1.5)

    # Генерация 4-значного кода
    code = str(random.randint(1000, 9999))

    # Сохраняем код в базе данных
    AuthCode.objects.update_or_create(phone_number=phone_number, defaults={'code': code})

    # Сохраняем номер телефона в сессии
    request.session['phone_number'] = phone_number

    # В реальной ситуации здесь была бы отправка кода пользователю, но мы просто возвращаем его
    return Response({"code": code}, status=status.HTTP_200_OK)


# Эмуляция проверки кода и авторизации пользователя
@api_view(['POST'])
def verify_code(request):
    """Проверка кода и авторизация пользователя"""
    entered_code = request.data.get('code')

    # Получаем номер телефона из сессии
    phone_number = request.session.get('phone_number')
    if not phone_number:
        return Response({"detail": "Phone number is missing. Please send it first."}, status=status.HTTP_400_BAD_REQUEST)

    if not entered_code:
        return Response({"detail": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        auth_code = AuthCode.objects.get(phone_number=phone_number)
        if auth_code.code != entered_code:
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)
    except AuthCode.DoesNotExist:
        return Response({"detail": "Code not found for this phone number."}, status=status.HTTP_404_NOT_FOUND)

    User = get_user_model()
    user, created = CustomUser.objects.get_or_create(username=phone_number, phone_number=phone_number)

    if created:
        invite_code_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        user.invite_code = invite_code_str
        user.save()

        # Создаем запись в модели InviteCode
        invite_code_instance = InviteCode(code=invite_code_str, creator=user)
        invite_code_instance.save()

    login(request, user)
    token, _ = Token.objects.get_or_create(user=user)

    return Response({"token": token.key}, status=status.HTTP_200_OK)


# Получение профиля пользователя
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Получение профиля пользователя"""
    user = request.user
    data = {
        "username": user.username,
        "phone_number": user.phone_number,
        "invite_code": user.invite_code,
        "used_invite_code": user.used_invite_code.code if user.used_invite_code else None,
        "users_activated_by_me": [u.phone_number for u in user.created_invite_code.users.all()] if hasattr(user, 'created_invite_code') else []
    }
    return Response(data, status=status.HTTP_200_OK)


# Активация инвайт-кода
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_invite_code(request):
    """Активация инвайт-кода"""
    code = request.data.get('code')

    if not code:
        return Response({"detail": "Invite code is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        invite_code = InviteCode.objects.get(code=code)
    except InviteCode.DoesNotExist:
        return Response({"detail": "Invalid invite code."}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if user.used_invite_code:
        return Response({"detail": "You have already activated an invite code."}, status=status.HTTP_400_BAD_REQUEST)

    user.used_invite_code = invite_code
    user.save()

    invite_code.users.add(user)

    return Response({"detail": "Invite code activated successfully."}, status=status.HTTP_200_OK)


def login_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        # Генерация 4-значного кода
        code = str(random.randint(1000, 9999))

        # Сохраняем код в базе данных
        AuthCode.objects.update_or_create(phone_number=phone_number, defaults={'code': code})

        # Сохраняем номер телефона в сессии
        request.session['phone_number'] = phone_number

        # Перенаправляем пользователя на страницу для ввода кода
        return redirect('code_verification')
    return render(request, 'login.html')


def verify_code_view(request):
    error_message = None

    if request.method == 'POST':
        # Получаем номер телефона из сессии
        phone_number = request.session.get('phone_number')
        if not phone_number:
            error_message = 'Phone number is missing. Please enter it first.'
            return render(request, 'login.html', {'error': error_message})

        entered_code = request.POST.get('code')

        try:
            auth_code = AuthCode.objects.get(phone_number=phone_number)
            if auth_code.code == entered_code:
                user, created = CustomUser.objects.get_or_create(username=phone_number, phone_number=phone_number)

                # Если пользователь только что был создан, генерируем для него инвайт-код
                if created:
                    invite_code_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
                    user.invite_code = invite_code_str
                    user.save()

                    # Создаем запись в модели InviteCode
                    invite_code_instance = InviteCode(code=invite_code_str, creator=user)
                    invite_code_instance.save()

                login(request, user)
                return redirect('profile_view')
            else:
                error_message = 'Invalid code. Please try again.'
        except AuthCode.DoesNotExist:
            error_message = 'Invalid code. Please try again.'

    return render(request, 'verify_code.html', {'error': error_message})


@login_required
def profile_view(request):
    error_message = None
    success_message = None
    activated_users = []

    if request.method == 'POST':
        code = request.POST.get('invite_code')
        try:
            invite_code = InviteCode.objects.get(code=code)
            if request.user.used_invite_code:
                error_message = "You have already activated an invite code."
            else:
                request.user.used_invite_code = invite_code
                request.user.save()
                invite_code.users.add(request.user)
                success_message = "Invite code activated successfully."
        except InviteCode.DoesNotExist:
            error_message = "Invalid invite code."

    if hasattr(request.user, 'created_invite_code'):
        activated_users = request.user.created_invite_code.users.all()

    return render(request, 'profile.html', {
        'error': error_message,
        'success': success_message,
        'activated_users': activated_users
    })



