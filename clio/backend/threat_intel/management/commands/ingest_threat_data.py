"""
Management command to download MITRE ATT&CK and NVD CVE data,
normalize them into JSONL files, and optionally build the Chroma vector
store index.

Usage:
    python manage.py ingest_threat_data            # download + build index
    python manage.py ingest_threat_data --skip-index  # download only
    python manage.py ingest_threat_data --skip-download  # index from existing JSONL
"""

from __future__ import annotations

import email.utils
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Download MITRE ATT&CK and NVD CVE data and build the RAG vector store."

    MITRE_URLS: dict[str, str] = {
        "enterprise-attack": (
            "https://github.com/mitre-attack/attack-stix-data/raw/master"
            "/enterprise-attack/enterprise-attack.json"
        ),
        "mobile-attack": (
            "https://github.com/mitre-attack/attack-stix-data/raw/master"
            "/mobile-attack/mobile-attack.json"
        ),
        "ics-attack": (
            "https://github.com/mitre-attack/attack-stix-data/raw/master"
            "/ics-attack/ics-attack.json"
        ),
    }

    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    NVD_PAGE_SIZE = 2000
    # NVD rate limits: 5 req/30s without key, 50 req/30s with key
    NVD_SLEEP_NO_KEY = 6      # seconds between requests (no API key)
    NVD_SLEEP_WITH_KEY = 0.6  # seconds between requests (API key present)

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-index",
            action="store_true",
            default=False,
            help="Download data but skip building the vector store index.",
        )
        parser.add_argument(
            "--skip-download",
            action="store_true",
            default=False,
            help="Skip downloading data; build index from existing JSONL files.",
        )

    def handle(self, *args, **options):
        build_index = not options["skip_index"]

        base = Path(settings.BASE_DIR) / "threat_data"
        base.mkdir(exist_ok=True)
        (base / "mitre").mkdir(exist_ok=True)
        (base / "nvd").mkdir(exist_ok=True)

        techniques: list[dict] = []
        cves: list[dict] = []

        if not options["skip_download"]:
            techniques = self._download_mitre(base)
            cves = self._download_nvd(base)

            self._write_jsonl(base / "mitre_techniques.jsonl", techniques)
            self._write_jsonl(base / "nvd_cves.jsonl", cves)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Written: {len(techniques)} techniques, {len(cves)} CVEs."
                )
            )
        else:
            self.stdout.write("Skipping download — reading existing JSONL files.")
            techniques = self._read_jsonl(base / "mitre_techniques.jsonl")
            cves = self._read_jsonl(base / "nvd_cves.jsonl")
            self.stdout.write(
                f"Loaded {len(techniques)} techniques, {len(cves)} CVEs from disk."
            )

        if build_index:
            self._build_index(base, techniques, cves)

    # -------------------------------------------------------------------------
    # MITRE ATT&CK
    # -------------------------------------------------------------------------

    def _download_mitre(self, base: Path) -> list[dict]:
        techniques: list[dict] = []
        errors = 0

        with httpx.Client(timeout=120, follow_redirects=True) as client:
            for domain, url in self.MITRE_URLS.items():
                dest = base / "mitre" / f"{domain}.json"
                self.stdout.write(f"Fetching MITRE {domain}…")

                # Conditional request: skip re-download if server says unchanged
                headers: dict[str, str] = {}
                if dest.exists():
                    mtime = dest.stat().st_mtime
                    headers["If-Modified-Since"] = email.utils.formatdate(
                        mtime, usegmt=True
                    )

                try:
                    resp = client.get(url, headers=headers)

                    if resp.status_code == 304:
                        self.stdout.write(f"  {domain}: unchanged (304), using cache.")
                        data = json.loads(dest.read_text(encoding="utf-8"))
                    elif resp.status_code == 200:
                        dest.write_bytes(resp.content)
                        data = resp.json()
                        self.stdout.write(
                            f"  {domain}: downloaded {len(resp.content):,} bytes."
                        )
                    else:
                        self.stderr.write(
                            f"  {domain}: unexpected HTTP {resp.status_code}, skipping."
                        )
                        errors += 1
                        continue

                except httpx.RequestError as exc:
                    self.stderr.write(f"  {domain}: network error — {exc}")
                    errors += 1
                    continue

                domain_techniques = self._extract_techniques(data, domain)
                techniques.extend(domain_techniques)
                self.stdout.write(
                    f"  {domain}: {len(domain_techniques)} techniques extracted."
                )

        if errors:
            self.stderr.write(f"MITRE: {errors} domain(s) had errors.")
        return techniques

    def _extract_techniques(self, stix_bundle: dict, domain: str) -> list[dict]:
        results: list[dict] = []
        for obj in stix_bundle.get("objects", []):
            if obj.get("type") != "attack-pattern":
                continue
            # Skip deprecated / revoked entries
            if obj.get("x_mitre_deprecated") or obj.get("revoked"):
                continue

            # ATT&CK external ID (e.g. T1059, T1059.001)
            ext_id = ""
            for ref in obj.get("external_references", []):
                if "mitre-attack" in ref.get("source_name", ""):
                    ext_id = ref.get("external_id", "")
                    break

            tactics = [
                kp["phase_name"] for kp in obj.get("kill_chain_phases", [])
            ]

            results.append(
                {
                    "id": obj.get("id", ""),
                    "name": obj.get("name", ""),
                    "description": obj.get("description", ""),
                    "tactic": tactics,
                    "platforms": obj.get("x_mitre_platforms", []),
                    "external_id": ext_id,
                    "domain": domain,
                }
            )
        return results

    # -------------------------------------------------------------------------
    # NVD CVE
    # -------------------------------------------------------------------------

    def _download_nvd(self, base: Path) -> list[dict]:
        api_key = os.environ.get("NVD_API_KEY", "")
        sleep_secs = self.NVD_SLEEP_WITH_KEY if api_key else self.NVD_SLEEP_NO_KEY

        last_sync_file = base / ".last_nvd_sync"
        params: dict[str, str | int] = {"resultsPerPage": self.NVD_PAGE_SIZE}

        if last_sync_file.exists():
            last_ts = last_sync_file.read_text().strip()
            now_ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
            params["lastModStartDate"] = last_ts
            params["lastModEndDate"] = now_ts
            self.stdout.write(f"NVD incremental sync from {last_ts}.")
        else:
            self.stdout.write("NVD full sync (no previous run timestamp found).")

        headers: dict[str, str] = {}
        if api_key:
            headers["apiKey"] = api_key

        cves: list[dict] = []
        start_index = 0
        total_results: int | None = None
        page_num = 0
        errors = 0

        with httpx.Client(timeout=60) as client:
            while True:
                params["startIndex"] = start_index
                self.stdout.write(
                    f"  NVD page {page_num} (startIndex={start_index})…"
                )

                try:
                    resp = client.get(self.NVD_API_URL, params=params, headers=headers)
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    self.stderr.write(f"  NVD page {page_num}: HTTP error — {exc}")
                    errors += 1
                    break
                except httpx.RequestError as exc:
                    self.stderr.write(
                        f"  NVD page {page_num}: network error — {exc}"
                    )
                    errors += 1
                    break

                data = resp.json()
                cache_file = base / "nvd" / f"page_{page_num}.json"
                cache_file.write_text(json.dumps(data), encoding="utf-8")

                if total_results is None:
                    total_results = data.get("totalResults", 0)
                    self.stdout.write(f"  NVD total results: {total_results:,}")

                page_cves = self._extract_cves(data)
                cves.extend(page_cves)
                self.stdout.write(
                    f"  Page {page_num}: {len(page_cves)} CVEs extracted."
                )

                start_index += self.NVD_PAGE_SIZE
                page_num += 1

                if total_results is not None and start_index >= total_results:
                    break  # all pages consumed — termination condition

                # Mandatory NVD rate-limit sleep
                time.sleep(sleep_secs)

        if errors == 0:
            now_ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
            last_sync_file.write_text(now_ts)
            self.stdout.write(f"NVD sync timestamp updated to {now_ts}.")

        self.stdout.write(f"NVD download: {len(cves)} CVEs, {errors} error(s).")
        return cves

    def _extract_cves(self, nvd_data: dict) -> list[dict]:
        results: list[dict] = []
        for vuln in nvd_data.get("vulnerabilities", []):
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")

            # Prefer English description
            description = ""
            for desc in cve.get("descriptions", []):
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break

            # CVSS score: try v3.1 → v3.0 → v2.0
            cvss_score = None
            metrics = cve.get("metrics", {})
            for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                entries = metrics.get(metric_key, [])
                if entries:
                    cvss_score = entries[0].get("cvssData", {}).get("baseScore")
                    break

            # Affected products from CPE match strings (capped to avoid bloat)
            products: list[str] = []
            for config in cve.get("configurations", []):
                for node in config.get("nodes", []):
                    for cpe_match in node.get("cpeMatch", []):
                        if cpe_match.get("vulnerable"):
                            products.append(cpe_match.get("criteria", ""))
                            if len(products) >= 20:
                                break

            results.append(
                {
                    "id": cve_id,
                    "description": description,
                    "cvss_score": cvss_score,
                    "published_date": cve.get("published", ""),
                    "affected_products": products,
                }
            )
        return results

    # -------------------------------------------------------------------------
    # JSONL helpers
    # -------------------------------------------------------------------------

    def _write_jsonl(self, path: Path, records: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict]:
        if not path.exists():
            self.stderr.write(f"File not found: {path}")
            return []
        records: list[dict] = []
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        self.stderr.write(f"Skipping malformed JSONL line: {exc}")
        return records

    # -------------------------------------------------------------------------
    # Vector store ingestion
    # -------------------------------------------------------------------------

    def _build_index(
        self, base: Path, techniques: list[dict], cves: list[dict]
    ) -> None:
        self.stdout.write("Building Chroma vector store index…")
        try:
            from threat_intel.rag import build_vector_store
        except ImportError as exc:
            self.stderr.write(
                f"RAG dependencies not installed: {exc}\n"
                "Run: pip install langchain-openai langchain-community chromadb "
                "sentence-transformers"
            )
            return

        build_vector_store(
            base, techniques, cves, stdout=self.stdout, stderr=self.stderr
        )
        self.stdout.write(self.style.SUCCESS("Vector store built successfully."))
