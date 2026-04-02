from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django import forms
import json

from django.urls import path
from logs.models import LogEntry
from operations.models import Operation
from common.redis_client import get_encrypted_redis
from accounts.htmx_auth import htmx_login_required

class LogForm(forms.ModelForm):
    class Meta:
        model = LogEntry
        fields = ['hostname', 'command', 'notes', 'status']

@htmx_login_required
def logs_page(request):
    try:
        redis_client = get_encrypted_redis()
        active_op_id = redis_client.get(f"user:{request.user.username}:active_operation")
        active_operation = Operation.objects.filter(id=active_op_id).first() if active_op_id else None
    except Exception:
        active_operation = None

    # Determine tag details to pass to template if active operation exists
    if active_operation:
        active_operation.operation_name = active_operation.name
        if hasattr(active_operation, 'tag') and active_operation.tag:
            active_operation.tag_name = active_operation.tag.name
            active_operation.tag_color = active_operation.tag.color

    return render(request, 'logs/index.html', {'active_operation': active_operation})

@require_http_methods(["GET"])
@htmx_login_required
def logs_list_htmx(request):
    qs = LogEntry.objects.all().order_by('-timestamp')

    hostname = request.GET.get('hostname')
    if hostname:
        qs = qs.filter(hostname__icontains=hostname)

    ip_address = request.GET.get('ip_address')
    if ip_address:
        qs = qs.filter(internal_ip__icontains=ip_address)

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    tag = request.GET.get('tag')
    if tag:
        qs = qs.filter(tags__name__icontains=tag)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Store filters for pagination links
    filters = {
        'hostname': hostname,
        'ip_address': ip_address,
        'status': status,
        'tag': tag
    }

    return render(request, 'logs/partials/list.html', {
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'filters': filters
    })

@require_http_methods(["GET"])
@htmx_login_required
def log_panel(request):
    log_id = request.GET.get('log_id')
    log = get_object_or_404(LogEntry, id=log_id) if log_id else None
    form = LogForm(instance=log)
    return render(request, 'logs/partials/panel.html', {'form': form, 'log': log})

@require_http_methods(["POST"])
@htmx_login_required
def log_save_htmx(request):
    log_id = request.POST.get('log_id')
    log = get_object_or_404(LogEntry, id=log_id) if log_id else None

    form = LogForm(request.POST, instance=log)
    if not form.is_valid():
        return render(request, 'logs/partials/panel.html', {'form': form, 'log': log}, status=400)

    try:
        log_entry = form.save(commit=False)
        if not log:
            log_entry.analyst = request.user.username
        log_entry.save()

        response = HttpResponse()
        response['HX-Trigger'] = 'logsUpdated'
        return response
    except Exception as e:
        return render(request, 'logs/partials/panel.html', {
            'form': form,
            'log': log,
            'error': str(e)
        }, status=400)

@require_http_methods(["DELETE"])
@htmx_login_required
def log_delete_htmx(request, log_id):
    log = get_object_or_404(LogEntry, id=log_id)
    log.delete()
    response = HttpResponse()
    response['HX-Trigger'] = 'logsUpdated'
    return response

@require_http_methods(["GET"])
@htmx_login_required
def log_toggle(request, log_id):
    # This just returns the log card but expanded
    log = get_object_or_404(LogEntry, id=log_id)
    # Note: State usually kept in client or session, but for HTMX we'll pass 'expanded=True' to the template
    # Here we simulate toggling by re-rendering a partial just for this log card.
    log.expanded = True
    return render(request, 'logs/partials/list.html', {'logs': [log]}) # Actually we need a specific partial for a single card

@require_http_methods(["GET"])
@htmx_login_required
def card_fields_modal(request):
    return render(request, 'logs/partials/card_fields_modal.html')

@require_http_methods(["POST"])
@htmx_login_required
def log_ai_context_htmx(request, log_id):
    from django.http import HttpResponse
    # Mocking AI Context Generation for the demo
    # In a full implementation, this triggers a Celery task or calls the LLM synchronously.
    html = """
    <div style="font-size: 0.9em; line-height: 1.5; padding: 1rem; background-color: rgba(59, 130, 246, 0.1); border-radius: 4px; border: 1px solid rgba(59, 130, 246, 0.3);">
        <strong>Summary:</strong> AI Analysis indicates potentially suspicious command execution.<br/>
        <strong>Score:</strong> <span class="badge" style="background-color: #f97316; color: white;">7.5 / 10</span><br/>
        <strong>MITRE Techniques:</strong>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.25rem;">
            <span class="badge" style="background-color: #3b82f622; color: #3b82f6; border: 1px solid #3b82f655;">T1059 - Command and Scripting Interpreter</span>
        </div>
    </div>
    """
    return HttpResponse(html)
