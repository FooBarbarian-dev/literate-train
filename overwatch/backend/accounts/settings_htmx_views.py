from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from accounts.backends import change_password, authenticate_user
from accounts.validators import validate_password
from rest_framework.exceptions import ValidationError
from accounts.htmx_auth import htmx_login_required

@require_http_methods(["GET"])
@htmx_login_required
def settings_page(request):
    return render(request, 'accounts/settings/index.html')

@require_http_methods(["POST"])
@htmx_login_required
def change_password_htmx(request):
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    if new_password != confirm_password:
        return render(request, 'accounts/settings/partials/password_form.html', {
            'message': 'New passwords do not match.',
            'message_type': 'error'
        }, status=200)

    try:
        validate_password(new_password)
    except ValidationError as e:
        err_msg = str(e.detail[0]) if hasattr(e, 'detail') else str(e)
        return render(request, 'accounts/settings/partials/password_form.html', {
            'message': err_msg,
            'message_type': 'error'
        }, status=200)

    auth_result = authenticate_user(request.user.username, current_password)
    if not auth_result:
        return render(request, 'accounts/settings/partials/password_form.html', {
            'message': 'Current password is incorrect.',
            'message_type': 'error'
        }, status=200)

    change_password(request.user.username, request.user.role, new_password)

    return render(request, 'accounts/settings/partials/password_form.html', {
        'message': 'Password changed successfully.',
        'message_type': 'success'
    })

@require_http_methods(["POST"])
@htmx_login_required
def logout_all_htmx(request):
    from accounts.jwt_utils import revoke_all_tokens_for_user
    from django.conf import settings as django_settings

    user = request.user
    if user and hasattr(user, "username"):
        revoke_all_tokens_for_user(user.username)

    response = HttpResponse()
    response['HX-Redirect'] = '/login/'
    samesite = "Lax" if django_settings.DEBUG else "Strict"
    response.delete_cookie("auth_token", samesite=samesite)
    response.delete_cookie("token", samesite=samesite)
    response.delete_cookie("_csrf", samesite=samesite)
    return response
