# Fix Progress

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | FK rename: Operation.tag_id → tag, UserOperation.operation_id → operation | ✅ Complete | Migration: 0003_rename_fk_fields (state-only RenameField, db_column preserved) |
| 2 | Register JWTCookieAuthentication in DRF settings | ✅ Complete | Added as first auth class in DEFAULT_AUTHENTICATION_CLASSES |
| 3 | Fix InputSanitizationMiddleware to use request.body | ✅ Complete | Replaced request.data access with request.body + json.loads |
| 4 | Fix locked_by = None → "" | ✅ Complete | logs/services.py toggle_lock now sets locked_by="" |
| 5 | Create admin.py files for all 8 backend models | ✅ Complete | 6 admin files: logs, api_keys, operations, tags, evidence, templates_mgmt |
| 6 | CSRF timing-safe comparison | ✅ Complete | Using secrets.compare_digest in common/middleware.py |
| 7 | Write automated tests | ✅ Complete | pytest.ini + conftest.py + 5 test files covering all specified cases |
| 8 | Remove Log.id AutoField override | ✅ Complete | Migration: 0002_remove_autofield_use_bigautofield (alters integer → bigint) |
| 9 | Adopt django-environ | ✅ Complete | All os.environ.get() replaced in base.py, development.py, production.py, redis_client.py, encryption.py, backends.py, jwt_utils.py, relation_service/settings.py |
| 10 | Stream exports, no temp files | ✅ Complete | Both ExportCSVView and ExportJSONView now use StreamingHttpResponse |
| 11 | Adopt django-storages for S3 | ✅ Complete | STORAGES config added, evidence/views.py uses default_storage, FileField added alongside existing CharField |
| 12 | Add app_name to all URL configs | ✅ Complete | 11 backend + 2 relation_service urls.py files updated |
| 13 | Replace unique_together with UniqueConstraint | ✅ Complete | operations (0004), tags (0004), relations (0002) migrations generated |
| 14 | Delete accounts/middleware.py dead code | ✅ Complete | Confirmed no references, file deleted |
| 15 | Adopt whitenoise for static files | ✅ Complete | WhiteNoiseMiddleware added after SecurityMiddleware, CompressedManifestStaticFilesStorage set |
| 16 | Pin Django 5.2 LTS and connection pooling | ✅ Complete | Django>=5.2,<5.3, CONN_MAX_AGE=600, CONN_HEALTH_CHECKS=True, pool=True |
| 17 | Replace signal thread-spawning with Celery | ✅ Complete | celery.py, tasks.py, signals.py rewritten, compose.yaml celery_worker added |

| 18 | Extend CLIO: BUG 1 (thread_id UUID→int), BUG 2 (per-session sources), BUG 3 (source_url citations), BUG 4 (AI Assist column visible by default) | ✅ Complete | Migration 0003, SessionSource model, ChatSessionSourcesView, tasks._store_session_sources, ThreatIntelPage updates |
| 19 | Admin pages for all threat_intel models (ChatSession, SessionSource, enhanced MitreTechnique/NvdCve) | ✅ Complete | threat_intel/admin.py rewritten; custom.css column rules added |

## DEPLOYMENT NOTES

### Item 8 — Log.id BigAutoField migration
- **Risk**: The migration alters the `logs.id` column from `integer` to `bigint`.
- **Impact**: This requires an `ALTER TABLE` which takes an `ACCESS EXCLUSIVE` lock on the `logs` table.
- **Recommendation**: Schedule during a maintenance window. For large tables, consider using `pg_repack` or a blue-green migration strategy.

### Item 11 — django-storages (S3)
- **Risk**: Existing evidence files stored on local disk will NOT be automatically migrated to S3.
- **Transition plan**: The old `filepath` CharField is preserved alongside the new `file` FileField. Existing files continue to work via `filepath`. New uploads go through `default_storage` (S3).
- **Data migration**: A separate data migration script should be written to:
  1. Read each `EvidenceFile.filepath` value
  2. Upload the file from local disk to S3
  3. Update the `file` field with the S3 path
  4. Once verified, the `filepath` CharField can be removed in a future migration.

### Item 17 — Celery worker
- **New process**: Production deployment now requires a Celery worker process.
- **Docker Compose**: `celery_worker` service added to `compose.yaml`.
- **Broker**: Uses Redis (same instance) on database 1.
- **Monitoring**: Consider adding Flower (`celery -A backend flower`) for task monitoring in production.
