from django.shortcuts import render
from django.views.decorators.http import require_http_methods

ALL_FIELDS = [
  { "name": 'id', "type": 'integer' },
  { "name": 'timestamp', "type": 'timestamp with time zone' },
  { "name": 'internal_ip', "type": 'character varying' },
  { "name": 'external_ip', "type": 'character varying' },
  { "name": 'mac_address', "type": 'character varying' },
  { "name": 'hostname', "type": 'character varying' },
  { "name": 'domain', "type": 'character varying' },
  { "name": 'username', "type": 'character varying' },
  { "name": 'command', "type": 'text' },
  { "name": 'notes', "type": 'text' },
  { "name": 'filename', "type": 'character varying' },
  { "name": 'status', "type": 'character varying' },
  { "name": 'hash_algorithm', "type": 'character varying' },
  { "name": 'hash_value', "type": 'character varying' },
  { "name": 'pid', "type": 'character varying' },
  { "name": 'analyst', "type": 'character varying' },
  { "name": 'locked', "type": 'boolean' },
  { "name": 'locked_by', "type": 'character varying' },
  { "name": 'created_at', "type": 'timestamp with time zone' },
  { "name": 'updated_at', "type": 'timestamp with time zone' },
]

DEFAULT_SELECTED = [
  'id', 'timestamp', 'hostname', 'domain', 'username',
  'command', 'filename', 'status', 'analyst',
]

from accounts.htmx_auth import htmx_login_required

@require_http_methods(["GET"])
@htmx_login_required
def export_page(request):
    half = (len(ALL_FIELDS) + 1) // 2
    left_fields = ALL_FIELDS[:half]
    right_fields = ALL_FIELDS[half:]

    return render(request, 'export/index.html', {
        'left_fields': left_fields,
        'right_fields': right_fields,
        'default_selected': DEFAULT_SELECTED,
        'total_fields': len(ALL_FIELDS),
    })
