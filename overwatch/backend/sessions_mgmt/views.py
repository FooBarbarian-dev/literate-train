import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsJWTAuthenticated, IsAdmin
from common.redis_client import get_encrypted_redis


class SessionListView(APIView):
    """List active sessions from Redis."""
    permission_classes = [IsJWTAuthenticated]

    @extend_schema(
        summary="List active sessions",
        tags=["sessions"],
    )
    def get(self, request):
        redis_client = get_encrypted_redis()

        session_keys = redis_client.scan_iter(match="session:*")
        sessions = []

        for key in session_keys:
            try:
                data = redis_client.get(key)
                if data:
                    session_info = json.loads(data)
                    session_info["session_key"] = key
                    sessions.append(session_info)
            except (json.JSONDecodeError, Exception):
                sessions.append({
                    "session_key": key,
                    "raw_data": data if data else None,
                })

        return Response({"sessions": sessions, "count": len(sessions)})


class SessionTerminateView(APIView):
    """Terminate a specific session (admin only)."""
    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Terminate a session (admin only)",
        tags=["sessions"],
    )
    def post(self, request):
        session_key = request.data.get("session_key")
        if not session_key:
            return Response(
                {"error": True, "message": "session_key is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        redis_client = get_encrypted_redis()

        if not redis_client.exists(session_key):
            return Response(
                {"error": True, "message": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        redis_client.delete(session_key)
        return Response({"message": f"Session {session_key} terminated"})
