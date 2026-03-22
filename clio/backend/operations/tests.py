"""Tests for the operations module: models, services, and API endpoints."""
import pytest

from operations.models import Operation, UserOperation
from tags.models import Tag


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestOperationModel:
    def test_create_operation(self, create_operation):
        op = create_operation(name="CRIMSON-HAWK")
        assert op.pk is not None
        assert op.is_active is True
        assert str(op) == "CRIMSON-HAWK"

    def test_unique_name(self, create_operation):
        create_operation(name="OP-UNIQUE")
        with pytest.raises(Exception):
            create_operation(name="OP-UNIQUE")


class TestUserOperationModel:
    def test_assign_user(self, create_operation, create_user_operation):
        op = create_operation(name="OP-ASSIGN")
        uo = create_user_operation("operator1", op)
        assert uo.username == "operator1"
        assert uo.operation_id == op

    def test_unique_constraint(self, create_operation, create_user_operation):
        op = create_operation(name="OP-DUP")
        create_user_operation("operator1", op)
        with pytest.raises(Exception):
            create_user_operation("operator1", op)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOperationListAPI:
    def test_list_operations(self, authenticated_client, create_operation):
        create_operation(name="OP-LIST-1")
        create_operation(name="OP-LIST-2")
        response = authenticated_client.get("/api/operations/")
        assert response.status_code == 200

    def test_unauthenticated_rejected(self, api_client):
        response = api_client.get("/api/operations/")
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestOperationCreateAPI:
    def test_admin_can_create(self, admin_client):
        response = admin_client.post(
            "/api/operations/",
            {"name": "NEW-OP", "description": "Test"},
            format="json",
        )
        assert response.status_code == 201
        assert Operation.objects.filter(name="NEW-OP").exists()
        # Should also create associated tag
        assert Tag.objects.filter(name="op:new-op").exists()

    def test_non_admin_cannot_create(self, authenticated_client):
        response = authenticated_client.post(
            "/api/operations/",
            {"name": "BLOCKED-OP"},
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestOperationDeactivateAPI:
    def test_admin_can_deactivate(self, admin_client, create_operation):
        op = create_operation(name="OP-DEACT")
        response = admin_client.delete(f"/api/operations/{op.pk}/")
        assert response.status_code == 204
        op.refresh_from_db()
        assert op.is_active is False
