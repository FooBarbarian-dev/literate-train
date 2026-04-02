from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.http import HttpResponse
from threat_intel.models import MitreTechnique, Cve, ChatSession, ChatMessage
from accounts.htmx_auth import htmx_login_required

@require_http_methods(["GET"])
@htmx_login_required
def threat_intel_page(request):
    return render(request, 'threat_intel/index.html', {'active_tab': 'mitre'})

@require_http_methods(["GET"])
@htmx_login_required
def mitre_tab(request):
    return render(request, 'threat_intel/partials/mitre_tab.html')

@require_http_methods(["GET"])
@htmx_login_required
def cves_tab(request):
    return render(request, 'threat_intel/partials/cves_tab.html')

@require_http_methods(["GET"])
@htmx_login_required
def assistant_tab(request):
    return render(request, 'threat_intel/partials/assistant_tab.html')

@require_http_methods(["GET"])
@htmx_login_required
def mitre_list_htmx(request):
    qs = MitreTechnique.objects.all().order_by('external_id')
    search = request.GET.get('search')
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(external_id__icontains=search)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'threat_intel/partials/mitre_list.html', {
        'techniques': page_obj.object_list,
        'page_obj': page_obj
    })

@require_http_methods(["GET"])
@htmx_login_required
def cves_list_htmx(request):
    qs = Cve.objects.all().order_by('-published_date')
    search = request.GET.get('search')
    if search:
        qs = qs.filter(cve_id__icontains=search) | qs.filter(description__icontains=search)

    # Severity filtering logic omitted for brevity in HTMX partial demo

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Process colors
    for cve in page_obj.object_list:
        score = cve.cvss_score
        if score is None: cve.cvss_color = '#6b7280'
        elif score >= 9.0: cve.cvss_color = '#ef4444'
        elif score >= 7.0: cve.cvss_color = '#f97316'
        elif score >= 4.0: cve.cvss_color = '#eab308'
        else: cve.cvss_color = '#22c55e'

    return render(request, 'threat_intel/partials/cves_list.html', {
        'cves': page_obj.object_list,
        'page_obj': page_obj
    })

from django.core.cache import cache
import json

@require_http_methods(["GET"])
@htmx_login_required
def chat_sessions_list(request):
    sessions = ChatSession.objects.filter(username=request.user.username).order_by('-updated_at')
    return render(request, 'threat_intel/partials/chat_sessions_list.html', {
        'sessions': sessions
    })

@require_http_methods(["POST"])
@htmx_login_required
def chat_session_create(request):
    session = ChatSession.objects.create(
        username=request.user.username,
        name="New conversation"
    )
    # Return the assistant tab but with the new session active
    response = render(request, 'threat_intel/partials/assistant_tab.html', {'active_session_id': session.id, 'session': session})
    return response

@require_http_methods(["GET"])
@htmx_login_required
def rag_panel_htmx(request):
    from threat_intel.views import RagStatusView
    from django.http import HttpRequest
    # Reuse the view logic for consistency
    rag_view = RagStatusView()
    rag_view.request = request
    try:
        response = rag_view.get(request)
        status_data = response.data
    except Exception:
        status_data = None

    session_id = request.GET.get('session_id')
    session_sources = {}
    if session_id:
        try:
            from threat_intel.models import SessionSource
            session = ChatSession.objects.get(id=session_id, username=request.user.username)
            mitre_qs = SessionSource.objects.filter(session=session, source_type=SessionSource.SOURCE_MITRE)
            nvd_qs = SessionSource.objects.filter(session=session, source_type=SessionSource.SOURCE_NVD)
            session_sources = {
                'mitre': {'count': mitre_qs.count()},
                'nvd': {'count': nvd_qs.count()}
            }
        except Exception:
            pass

    return render(request, 'threat_intel/partials/rag_panel.html', {
        'status': status_data,
        'session_sources': session_sources
    })

@require_http_methods(["GET"])
@htmx_login_required
def chat_session_load(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, username=request.user.username)
    return render(request, 'threat_intel/partials/chat_area.html', {'session': session})

@require_http_methods(["GET"])
@htmx_login_required
def chat_session_messages_htmx(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, username=request.user.username)
    qs = ChatMessage.objects.filter(session=session).order_by('created_at').values('message', 'created_at')

    messages = []
    for m in qs:
        try:
            raw = m["message"]
            if isinstance(raw, str):
                raw = json.loads(raw)
            msg_type = raw.get("type", "")
            if msg_type in ["human", "ai"]:
                role = "user" if msg_type == "human" else "assistant"
                messages.append({"role": role, "content": raw.get("content", "")})
        except Exception:
            continue

    return render(request, 'threat_intel/partials/chat_messages.html', {
        'session': session,
        'messages': messages
    })

@require_http_methods(["POST"])
@htmx_login_required
def chat_send_message(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, username=request.user.username)
    message = request.POST.get("message", "").strip()

    if not message:
        return HttpResponse("Message cannot be empty", status=400)

    if not session.name or session.name == "New conversation":
        session.name = (message[:57] + "…") if len(message) > 57 else message
        session.save(update_fields=["name", "updated_at"])

    # Attempt to dispatch celery task
    try:
        from threat_intel.tasks import run_chat_task
        from django_ai_assistant.models import Thread
        from threat_intel.assistants import CveAttackAssistant

        if session.thread_id is None:
            thread = Thread.objects.create()
            session.thread_id = thread.id
            session.save(update_fields=["thread_id"])
            assistant = CveAttackAssistant(thread_id=thread.id)
            assistant._init_history()

        task = run_chat_task.delay(message, session.thread_id, session_id=session.id)
        task_id = task.id
    except Exception as e:
        return render(request, 'threat_intel/partials/chat_messages.html', {
            'session': session,
            'error': f"Failed to queue task: {str(e)}"
        })

    # Optimistically append user message since DB insert happens in task
    # For appending via HX-Swap=beforeend, we only return the NEW message
    # AND the polling indicator.
    messages = [{"role": "user", "content": message}]

    response = render(request, 'threat_intel/partials/chat_messages.html', {
        'session': session,
        'messages': messages,
        'task_id': task_id
    })

    # If the session name changed, trigger sidebar reload
    response['HX-Trigger'] = 'reloadSessions'
    return response

@require_http_methods(["GET"])
@htmx_login_required
def chat_poll_task(request, session_id, task_id):
    session = get_object_or_404(ChatSession, id=session_id, username=request.user.username)
    result = cache.get(f"chat_task:{task_id}")

    if result is None or result.get("status") in ["pending", "running"]:
        # Still running, return the polling indicator again which replaces itself via outerHTML
        return render(request, 'threat_intel/partials/chat_polling.html', {
            'session': session,
            'task_id': task_id,
        })

    # Task finished (complete or error)
    # If error, render an error message to replace the indicator.
    # If success, render the single new message bubble to replace the indicator.
    if result.get("status") == "error":
        error_msg = result.get("error", "The assistant encountered an error.")
        html = f'<div class="alert alert-error chat-alert" style="margin-top: 1rem;">{error_msg}</div>'
        return HttpResponse(html)

    reply = result.get("reply", "")
    # Note: HTMX allows us to trigger an event (e.g. reload RAG Panel) when swapping this in
    response = render(request, 'threat_intel/partials/chat_messages.html', {
        'session': session,
        'messages': [{"role": "assistant", "content": reply}],
    })

    # We want to JUST return the bubble, not the whole container list.
    # The simplest way is to manually format the bubble or have a dedicated bubble template.
    # Since chat_messages loops over messages, we can just return it, BUT wait, chat_messages
    # has a container div class="chat-messages". Let's just return the raw HTML bubble to avoid nested containers:
    html = f"""
    <div class="chat-bubble chat-bubble-assistant">
        <div class="chat-bubble-label">Assistant</div>
        <div class="chat-bubble-content" style="white-space: pre-wrap; font-family: var(--font-mono);">{reply}</div>
    </div>
    """

    # Trigger RAG Panel reload so source counts update automatically!
    response = HttpResponse(html)
    response['HX-Trigger'] = 'reloadRagPanel'
    return response
