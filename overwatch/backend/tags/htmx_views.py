from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from tags.models import Tag
from tags.forms import TagForm
from accounts.htmx_auth import htmx_login_required

@htmx_login_required
def tags_page(request):
    return render(request, 'tags/index.html')

from django.db.models import Count

@require_http_methods(["GET"])
@htmx_login_required
def tags_list_htmx(request):
    search_query = request.GET.get('search', '')

    tags = Tag.objects.annotate(
        usage_count=Count("log_tags")
    )
    if search_query:
        tags = tags.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return render(request, 'tags/partials/list.html', {
        'tags': tags,
        'search': search_query
    })

@require_http_methods(["GET"])
@htmx_login_required
def create_tag_modal(request):
    form = TagForm(initial={'color': '#3b82f6'})
    return render(request, 'tags/partials/create_modal.html', {'form': form})

@require_http_methods(["POST"])
@htmx_login_required
def create_tag_htmx(request):
    form = TagForm(request.POST)
    if not form.is_valid():
        return render(request, 'tags/partials/create_modal.html', {'form': form}, status=200)

    try:
        tag = form.save(commit=False)
        tag.created_by = request.user.username
        tag.save()

        response = HttpResponse()
        response['HX-Trigger'] = 'tagsUpdated'
        return response
    except Exception as e:
        return render(request, 'tags/partials/create_modal.html', {
            'form': form,
            'error': str(e)
        }, status=200)
