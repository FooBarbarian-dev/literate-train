**DIAGNOSIS SUMMARY**
The sustained high resource usage on startup is primarily caused by a combination of missing container resource limits and uncapped concurrency settings in the worker layers (Celery and Gunicorn) combined with a severe memory leak from `DEBUG=True` being active in the default development profile. Because Docker containers without resource limits inherit the host's CPU core count, the unconfigured Celery and Gunicorn setups will spawn workers based on the host core count, multiplying the footprint of the application. The continuous churn of database connections (CONN_MAX_AGE=0) and the execution of heavy initialization tasks on every startup further drive up CPU usage.

**FINDINGS**

- **Location:** `clio/compose.yaml` (all services)
- **Issue:** No resource limits (CPU or memory) are defined for any service in Docker Compose.
- **Impact:** Both (Memory & CPU) - Without limits, containers will compete for all available host resources. Heavy services like Postgres, Redis, and unconstrained Python applications will consume unlimited memory under load, leading to eventual out-of-memory issues or host starvation.
- **Type:** Config problem
- **Fix:** Add `deploy.resources.limits` to each service in `clio/compose.yaml`.
```yaml
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

- **Location:** `clio/backend/entrypoint.sh` (Line 9 & 32) and `clio/backend/backend/settings/development.py` (Line 7)
- **Issue:** `DJANGO_SETTINGS_MODULE` defaults to `backend.settings.development`, which has `DEBUG = True`.
- **Impact:** Memory - Django stores every SQL query in memory when `DEBUG` is True. In a long-running process like Gunicorn or Celery, this results in a continuous, unbounded memory leak that grows with every request or task.
- **Type:** App problem / Config problem
- **Fix:** Set `DEBUG=False` or change the environment to production settings in Docker.
```bash
# In clio/backend/entrypoint.sh, either remove the default or change to production:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')
```

- **Location:** `clio/compose.yaml` (Line 41 - `celery_worker` command)
- **Issue:** Celery worker lacks concurrency limits (`-c`), which makes it default to the number of CPU cores. It also uses the default prefork pool.
- **Impact:** Memory - The worker process silently inherits the host's CPU core count. If the host has 16 cores, Celery forks 16 copies of the Django application into RAM on startup, vastly increasing baseline memory consumption.
- **Type:** Config problem
- **Fix:** Add an explicit concurrency limit to the worker command.
```yaml
    command: celery -A backend worker --loglevel=info -c 2
```

- **Location:** `clio/backend/entrypoint.sh` (Line 57)
- **Issue:** The Gunicorn command uses `-w 4`, hardcoding four worker processes. Combined with missing limits, this forces 4 full Django copies into memory.
- **Impact:** Memory - Hardcoding `-w 4` may be overkill depending on available memory. If paired with the `UvicornWorker` class, the app memory footprint is strictly `4 * (App Size)`.
- **Type:** Config problem
- **Fix:** Adjust worker count based on expected environment or use an environment variable.
```bash
exec gunicorn backend.asgi:application \
    -w ${WEB_CONCURRENCY:-2} \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:3001
```

- **Location:** `clio/backend/backend/settings/base.py` (Line 90)
- **Issue:** `CONN_MAX_AGE` is set to `0`.
- **Impact:** CPU - Setting this to `0` causes Django to close and reopen the database connection on every single request. At high load, connection overhead becomes a significant CPU burden for both Django and Postgres.
- **Type:** App problem
- **Fix:** Increase `CONN_MAX_AGE` to allow persistent connections.
```python
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
```

- **Location:** `clio/backend/entrypoint.sh` (Lines 18-54)
- **Issue:** The entrypoint script runs heavy commands (`migrate`, `collectstatic`, password seeding, and user creation) on every single `docker compose up`.
- **Impact:** CPU - These operations trigger full Django startups and expensive I/O or DB transactions on every boot, extending startup times and spiking CPU during container restarts.
- **Type:** Config problem
- **Fix:** Isolate initial startup logic. Use checks to see if the operations have already been run, or move `migrate` to a dedicated initialization container or CI/CD step rather than executing it dynamically on every boot.
```bash
# Example logic wrap for migrations:
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "==> Running migrations..."
    python manage.py migrate --noinput
fi
```

**CLEAN BILL OF HEALTH**
- **Redis Configuration:** Redis has explicit configuration with `--maxmemory 512mb` and `--maxmemory-policy noeviction`. It will not consume infinite RAM (though `noeviction` means tasks will fail when it fills up, rather than OOMing the host).
- **Gunicorn Workers Class:** Gunicorn correctly uses `uvicorn.workers.UvicornWorker` for ASGI compatibility.

**INCONCLUSIVE**
- **Custom Postgres Environment Variables:** The `db` service relies on default Postgres Docker configurations without custom environment variables like `POSTGRES_SHARED_BUFFERS` or `POSTGRES_WORK_MEM`, making it use conservative defaults. Better performance could be tuned, but without a specific workload profile, determining the exact impact is inconclusive.
- **.env contents:** We couldn't verify the actual environment variables provided in `./backend/.env` because it is not checked into source control. Values like `POSTGRES_PASSWORD` or any user overrides are unknown.