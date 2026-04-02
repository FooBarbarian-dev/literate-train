from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from accounts.htmx_auth import htmx_login_required
from api_keys.models import ApiKey
import hashlib
import secrets

@require_http_methods(["POST"])
@htmx_login_required
def generate_key_htmx(request):
    try:
        raw_key = secrets.token_urlsafe(48)
        key_id = secrets.token_urlsafe(16)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        ApiKey.objects.create(
            name="Generated Key",
            key_id=key_id,
            key_hash=key_hash,
            created_by=request.user.username,
            permissions=["logs:write"]
        )
        return render(request, 'accounts/settings/partials/api_keys.html', {
            'api_key': raw_key
        })
    except Exception as e:
        return render(request, 'accounts/settings/partials/api_keys.html', {
            'error': str(e)
        }, status=200)

@require_http_methods(["POST"])
@htmx_login_required
def revoke_keys_htmx(request):
    try:
        ApiKey.objects.filter(created_by=request.user.username, is_active=True).update(is_active=False)
        return render(request, 'accounts/settings/partials/api_keys.html', {})
    except Exception as e:
        return render(request, 'accounts/settings/partials/api_keys.html', {
            'error': str(e)
        }, status=200)
