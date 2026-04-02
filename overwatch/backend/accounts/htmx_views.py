import secrets
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.conf import settings as django_settings
from accounts.forms import LoginForm
from accounts.backends import authenticate_user
from accounts.jwt_utils import issue_token, revoke_token

def login_page(request):
    if hasattr(request.user, "is_authenticated") and request.user.is_authenticated:
        return redirect('logs-page')  # Assuming this URL exists or will exist
    form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@require_http_methods(["POST"])
def auth_login_htmx(request):
    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(request, 'accounts/partials/login_form.html', {'form': form}, status=200)

    username = form.cleaned_data['username']
    password = form.cleaned_data['password']

    auth_result = authenticate_user(username, password)
    if not auth_result:
        return render(request, 'accounts/partials/login_form.html', {
            'form': form,
            'error': "Invalid credentials. Please try again."
        }, status=200)

    token, payload = issue_token(auth_result["username"], auth_result["role"])
    csrf_token = secrets.token_hex(32)

    # Instead of rendering a template, we tell HTMX to redirect the user
    response = HttpResponse()
    response['HX-Redirect'] = '/logs/' # Target URL after login

    secure_cookie = not django_settings.DEBUG
    samesite = "Lax" if not secure_cookie else "Strict"
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
        max_age=8 * 3600,
    )
    response.set_cookie(
        "token",
        token,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
        max_age=8 * 3600,
    )
    response.set_cookie(
        "_csrf",
        csrf_token,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
        max_age=15 * 60,
    )

    return response

@require_http_methods(["POST"])
def auth_logout_htmx(request):
    user = request.user
    if user and hasattr(user, "jti") and hasattr(user, "username"):
        revoke_token(user.jti, user.username)

    response = HttpResponse()
    response['HX-Redirect'] = '/login/'
    samesite = "Lax" if django_settings.DEBUG else "Strict"
    response.delete_cookie("auth_token", samesite=samesite)
    response.delete_cookie("token", samesite=samesite)
    response.delete_cookie("_csrf", samesite=samesite)
    return response
