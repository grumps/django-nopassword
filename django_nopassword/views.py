# -*- coding: utf-8 -*-
import json
from django.conf import settings
from django.contrib.auth.views import login as django_login
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.http import HttpResponse

from django_nopassword.forms import AuthenticationForm
from django_nopassword.utils import USERNAME_FIELD, get_username
from django_nopassword.models import LoginCode
from django_nopassword.utils import User


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            code = LoginCode.objects.filter(**{'user__%s' % USERNAME_FIELD: request.POST.get('username')})[0]
            code.next = request.GET.get('next')
            code.save()
            code.send_login_email()
            return render(request, 'registration/sent_mail.html')

    return django_login(request, authentication_form=AuthenticationForm)


def login_with_code(request, login_code):
    code = get_object_or_404(LoginCode.objects.select_related('user'), code=login_code)
    return login_with_code_and_username(request, username=get_username(code.user), login_code=login_code)


def login_with_code_and_username(request, username, login_code):
    code = get_object_or_404(LoginCode, code=login_code)
    user = authenticate(**{USERNAME_FIELD: username, 'code': login_code})
    if user is None:
        raise Http404
    user = auth_login(request, user)
    return redirect(code.next)


def logout(request, redirect_to=None):
    auth_logout(request)
    if redirect_to is None:
        return redirect(reverse('login'))

    else:
        return redirect(redirect_to)


def users_json(request):
    if not getattr(settings, 'NOPASSWORD_AUTOCOMPLETE', False):
        raise Http404

    users = []
    for user in User.objects.filter(is_active=True):
        users.append({
            'value': user.username,
            'username': user.username,
            'full_name': user.get_full_name(),
        })

    return HttpResponse(json.dumps(users), mimetype="application/json")
