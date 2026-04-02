from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Count

from operations.models import Operation, UserOperation
from operations.forms import OperationForm
from operations.services import create_operation, set_active_operation
from common.redis_client import get_encrypted_redis
from accounts.htmx_auth import htmx_login_required

@htmx_login_required
def operations_page(request):
    return render(request, 'operations/index.html')

@require_http_methods(["GET"])
@htmx_login_required
def operations_list_htmx(request):
    ops = Operation.objects.filter(is_active=True).annotate(
        user_count=Count("user_operations")
    ).prefetch_related('user_operations__user')

    try:
        redis_client = get_encrypted_redis()
        active_op_id = redis_client.get(f"user:{request.user.username}:active_operation")
    except Exception:
        active_op_id = None

    operations_data = []
    for op in ops:
        users = [uo.user.username for uo in op.user_operations.all()]
        operations_data.append({
            'id': op.id,
            'name': op.name,
            'description': op.description,
            'created_at': op.created_at,
            'users': users,
            'is_user_active': str(op.id) == active_op_id
        })

    return render(request, 'operations/partials/list.html', {'operations': operations_data})

@require_http_methods(["GET"])
@htmx_login_required
def create_operation_modal(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin only")
    form = OperationForm()
    return render(request, 'operations/partials/create_modal.html', {'form': form})

@require_http_methods(["POST"])
@htmx_login_required
def create_operation_htmx(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin only")

    form = OperationForm(request.POST)
    if not form.is_valid():
        return render(request, 'operations/partials/create_modal.html', {'form': form}, status=200)

    try:
        create_operation(
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            created_by=request.user.username
        )

        # Return success with HX-Trigger to refresh the operations list and close the modal
        response = HttpResponse()
        response['HX-Trigger'] = 'operationsUpdated'
        # Close the modal by sending empty content back to the modal container (handled by client logic or empty swap)
        # We can also just send an empty string
        return response
    except Exception as e:
        return render(request, 'operations/partials/create_modal.html', {
            'form': form,
            'error': str(e)
        }, status=200)

@require_http_methods(["POST"])
@htmx_login_required
def set_active_htmx(request, operation_id):
    success = set_active_operation(request.user.username, operation_id)
    if not success:
        response = HttpResponse("<div class='alert alert-error'>Failed to set active operation</div>")
        return response

    response = HttpResponse()
    # Trigger a re-fetch of the operations list to update the UI
    response['HX-Trigger'] = 'operationsUpdated'
    return response
