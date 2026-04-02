from functools import wraps
from django.http import HttpResponse, HttpResponseRedirect
from accounts.authentication import JWTUser

def htmx_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # We need to verify standard Django request.user or our custom auth
        # Since we use DRF and JWT, request.user might not be populated by standard middleware
        # in the same way, but the frontend was using the cookie. We need to parse it.
        from accounts.jwt_utils import verify_token

        token = request.COOKIES.get('auth_token') or request.COOKIES.get('token')

        if not token:
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = '/login/'
                return response
            return HttpResponseRedirect('/login/')

        try:
            payload = verify_token(token)
            # Create a mock user object to satisfy the views
            request.user = JWTUser(payload)
        except Exception:
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = '/login/'
                return response
            return HttpResponseRedirect('/login/')

        return view_func(request, *args, **kwargs)
    return _wrapped_view
