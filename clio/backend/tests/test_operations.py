import pytest
from operations.models import Operation, UserOperation
from operations.serializers import OperationSerializer


@pytest.mark.django_db
class TestOperationFK:
    def test_operation_fk_select_related(self, make_tag, make_operation):
        """Catches the FK naming bug: select_related('tag') must work."""
        tag = make_tag(name="op-tag")
        op = make_operation(name="fk-test-op", tag=tag)
        queried = (
            Operation.objects.filter(pk=op.pk)
            .select_related("tag")
            .first()
        )
        assert queried.tag.name == "op-tag"

    def test_user_operation_fk(self, make_operation, make_user_operation):
        """UserOperation.operation returns the Operation instance."""
        op = make_operation(name="user-op-test")
        user_op = make_user_operation(operation=op, username="fk-user")
        assert user_op.operation == op
        assert user_op.operation.name == "user-op-test"

    def test_operation_serializer_tag_fields(self, make_tag, make_operation):
        """Serialized Operation must include tag_name and tag_color when tag is set."""
        tag = make_tag(name="ser-tag", color="#00FF00")
        op = make_operation(name="ser-test-op", tag=tag)
        queried = (
            Operation.objects.filter(pk=op.pk)
            .select_related("tag")
            .first()
        )
        data = OperationSerializer(queried).data
        assert data["tag_name"] == "ser-tag"
        assert data["tag_color"] == "#00FF00"
