from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """5 login attempts per 15 minutes per IP."""
    rate = "5/15min"
    scope = "auth"

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        num, period = rate.split("/")
        num_requests = int(num)
        # Handle custom period formats like "15min"
        if period.endswith("min"):
            duration = int(period[:-3]) * 60
        elif period.endswith("h"):
            duration = int(period[:-1]) * 3600
        else:
            duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(period, 1)
        return (num_requests, duration)


class TokenRefreshThrottle(AnonRateThrottle):
    """5 refresh attempts per 10 minutes per user."""
    rate = "5/10min"
    scope = "token_refresh"

    def get_cache_key(self, request, view):
        user = request.user
        if user and hasattr(user, "username"):
            return self.cache_format % {"scope": self.scope, "ident": user.username}
        return self.get_ident(request)

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        num, period = rate.split("/")
        num_requests = int(num)
        if period.endswith("min"):
            duration = int(period[:-3]) * 60
        else:
            duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(period, 1)
        return (num_requests, duration)
