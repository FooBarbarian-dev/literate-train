from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from api_keys.services import generate_api_key, revoke_all_keys
from accounts.htmx_auth import htmx_login_required

@require_http_methods(["POST"])
@htmx_login_required
def generate_key_htmx(request):
    try:
        api_key, raw_token = generate_api_key(
            name="Generated Key",
            created_by=request.user.username,
            expires_at=None
        )
        return render(request, 'accounts/settings/partials/api_keys.html', {
            'api_key': raw_token
        })
    except Exception as e:
        return render(request, 'accounts/settings/partials/api_keys.html', {
            'error': str(e)
        }, status=400)

@require_http_methods(["POST"])
@htmx_login_required
def revoke_keys_htmx(request):
    try:
        count = revoke_all_keys(request.user.username)
        return render(request, 'accounts/settings/partials/api_keys.html', {})
    except Exception as e:
        return render(request, 'accounts/settings/partials/api_keys.html', {
            'error': str(e)
        }, status=400)
