"""Minimal Search Console read and sitemap-submit surface."""

from __future__ import annotations

from datetime import date
import math
from urllib.parse import quote

from .http import GoogleApiClient
from .output import AdapterError
from .plans import canonical_site_url, canonical_target_url, property_contains, target_fingerprint


WEBMASTERS_BASE = "https://www.googleapis.com/webmasters/v3"
INSPECTION_URL = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
ALLOWED_SEARCH_DIMENSIONS = frozenset({"country", "date", "device", "page", "query", "searchAppearance"})
ALLOWED_SEARCH_TYPES = frozenset({"WEB", "IMAGE", "VIDEO", "NEWS", "DISCOVER", "GOOGLE_NEWS"})
ALLOWED_DATA_STATES = frozenset({"ALL", "FINAL"})
ALLOWED_AGGREGATION_TYPES = frozenset({"AUTO", "BY_PAGE", "BY_PROPERTY", "BY_NEWS_SHOWCASE_PANEL"})
RESPONSE_AGGREGATION_ALIASES = {
    "AUTO": "AUTO",
    "BY_PAGE": "BY_PAGE",
    "BY_PROPERTY": "BY_PROPERTY",
    "BY_NEWS_SHOWCASE_PANEL": "BY_NEWS_SHOWCASE_PANEL",
    "auto": "AUTO",
    "byPage": "BY_PAGE",
    "byProperty": "BY_PROPERTY",
    "byNewsShowcasePanel": "BY_NEWS_SHOWCASE_PANEL",
}


def _search_input_error(next_step: str) -> AdapterError:
    return AdapterError("invalid_input", "blocked", 12, next_step)


def search_analytics_query(
    *,
    start_date: str,
    end_date: str,
    dimensions: list[str] | tuple[str, ...] | None = None,
    search_type: str = "WEB",
    data_state: str = "FINAL",
    aggregation_type: str = "AUTO",
    row_limit: int = 1000,
    start_row: int = 0,
) -> dict[str, object]:
    parsed_dates: list[date] = []
    for value in (start_date, end_date):
        if not isinstance(value, str):
            raise _search_input_error("Use exact YYYY-MM-DD dates for Search Analytics.")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise _search_input_error("Use exact YYYY-MM-DD dates for Search Analytics.") from exc
        if parsed.isoformat() != value:
            raise _search_input_error("Use exact YYYY-MM-DD dates for Search Analytics.")
        parsed_dates.append(parsed)
    if parsed_dates[0] > parsed_dates[1]:
        raise _search_input_error("Search Analytics start date must not be after the end date.")

    normalized_dimensions = list(dimensions or [])
    if any(not isinstance(value, str) or value not in ALLOWED_SEARCH_DIMENSIONS for value in normalized_dimensions):
        raise _search_input_error("Use only the fixed Search Analytics dimension allowlist.")
    if len(set(normalized_dimensions)) != len(normalized_dimensions):
        raise _search_input_error("Do not repeat a Search Analytics dimension.")
    if search_type not in ALLOWED_SEARCH_TYPES:
        raise _search_input_error("Use only a supported Search Analytics search type.")
    if data_state not in ALLOWED_DATA_STATES:
        raise _search_input_error("Use FINAL or ALL for Search Analytics data state.")
    if aggregation_type not in ALLOWED_AGGREGATION_TYPES:
        raise _search_input_error("Use only a supported Search Analytics aggregation type.")
    if isinstance(row_limit, bool) or not isinstance(row_limit, int) or not 1 <= row_limit <= 25000:
        raise _search_input_error("Search Analytics row limit must be between 1 and 25000.")
    if isinstance(start_row, bool) or not isinstance(start_row, int) or start_row < 0:
        raise _search_input_error("Search Analytics start row must be zero or greater.")

    return {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": normalized_dimensions,
        "type": search_type,
        "dataState": data_state,
        "aggregationType": aggregation_type,
        "rowLimit": row_limit,
        "startRow": start_row,
    }


def _search_metric(row: dict[str, object], key: str) -> float:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise AdapterError("provider_rejected", "failed", 14, "A Search Analytics row contained an invalid metric.")
    return float(value)


def _site_summary(item: object) -> dict[str, object] | None:
    if not isinstance(item, dict) or not isinstance(item.get("siteUrl"), str):
        return None
    return {
        "site_url": canonical_site_url(item["siteUrl"]),
        "permission_level": str(item.get("permissionLevel", "unknown")),
    }


def _sitemap_summary(item: object) -> dict[str, object] | None:
    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
        return None
    return {
        "path": canonical_target_url(item["path"]),
        "last_submitted": item.get("lastSubmitted") if isinstance(item.get("lastSubmitted"), str) else None,
        "last_downloaded": item.get("lastDownloaded") if isinstance(item.get("lastDownloaded"), str) else None,
        "is_pending": bool(item.get("isPending", False)),
        "is_sitemaps_index": bool(item.get("isSitemapsIndex", False)),
        "type": str(item.get("type", "unknown")),
        "warnings": int(item.get("warnings", 0)) if str(item.get("warnings", "0")).isdigit() else None,
        "errors": int(item.get("errors", 0)) if str(item.get("errors", "0")).isdigit() else None,
    }


class GSCClient:
    def __init__(self, api: GoogleApiClient) -> None:
        self._api = api

    def list_sites(self) -> list[dict[str, object]]:
        payload = self._api.request_json("GET", f"{WEBMASTERS_BASE}/sites")
        if not isinstance(payload, dict):
            return []
        sites = payload.get("siteEntry", [])
        if not isinstance(sites, list):
            return []
        return [summary for item in sites if (summary := _site_summary(item)) is not None]

    def get_site(self, site_url: str, *, allow_not_found: bool = False) -> dict[str, object] | None:
        site = canonical_site_url(site_url)
        payload = self._api.request_json(
            "GET",
            f"{WEBMASTERS_BASE}/sites/{quote(site, safe='')}",
            allow_not_found=allow_not_found,
        )
        if payload is None:
            return None
        summary = _site_summary(payload)
        if summary is None:
            raise AdapterError("provider_rejected", "failed", 14, "The Search Console site response lacked an exact property identifier.")
        if summary["site_url"] != site:
            raise AdapterError("target_mismatch", "blocked", 12, "The provider returned a different Search Console property.")
        return summary

    def list_sitemaps(self, site_url: str) -> list[dict[str, object]]:
        site = canonical_site_url(site_url)
        payload = self._api.request_json("GET", f"{WEBMASTERS_BASE}/sites/{quote(site, safe='')}/sitemaps")
        if not isinstance(payload, dict):
            return []
        sitemaps = payload.get("sitemap", [])
        if not isinstance(sitemaps, list):
            return []
        return [summary for item in sitemaps if (summary := _sitemap_summary(item)) is not None]

    def get_sitemap(
        self,
        site_url: str,
        sitemap_url: str,
        *,
        allow_not_found: bool = False,
    ) -> dict[str, object] | None:
        site = canonical_site_url(site_url)
        sitemap = canonical_target_url(sitemap_url)
        if not property_contains(site, sitemap):
            raise AdapterError("target_mismatch", "blocked", 12, "The sitemap URL is outside the exact Search Console property scope.")
        payload = self._api.request_json(
            "GET",
            f"{WEBMASTERS_BASE}/sites/{quote(site, safe='')}/sitemaps/{quote(sitemap, safe='')}",
            allow_not_found=allow_not_found,
        )
        if payload is None:
            return None
        summary = _sitemap_summary(payload)
        if summary is None or summary["path"] != sitemap:
            raise AdapterError("target_mismatch", "blocked", 12, "The provider returned a different sitemap resource.")
        return summary

    def submit_sitemap(self, site_url: str, sitemap_url: str) -> None:
        site = canonical_site_url(site_url)
        sitemap = canonical_target_url(sitemap_url)
        if not property_contains(site, sitemap):
            raise AdapterError("target_mismatch", "blocked", 12, "The sitemap URL is outside the exact Search Console property scope.")
        self._api.request_json(
            "PUT",
            f"{WEBMASTERS_BASE}/sites/{quote(site, safe='')}/sitemaps/{quote(sitemap, safe='')}",
        )

    def inspect_url(self, site_url: str, inspection_url: str) -> dict[str, object]:
        site = canonical_site_url(site_url)
        target = canonical_target_url(inspection_url)
        if not property_contains(site, target):
            raise AdapterError("target_mismatch", "blocked", 12, "The inspection URL is outside the exact Search Console property scope.")
        payload = self._api.request_json(
            "POST",
            INSPECTION_URL,
            body={"inspectionUrl": target, "siteUrl": site},
            read_only=True,
        )
        if not isinstance(payload, dict):
            raise AdapterError("provider_rejected", "failed", 14, "The URL Inspection response was empty.")
        inspection = payload.get("inspectionResult")
        if not isinstance(inspection, dict):
            raise AdapterError("provider_rejected", "failed", 14, "The URL Inspection response lacked inspectionResult.")
        index = inspection.get("indexStatusResult")
        if not isinstance(index, dict):
            index = {}
        allowed = {
            "verdict": "verdict",
            "coverageState": "coverage_state",
            "robotsTxtState": "robots_txt_state",
            "indexingState": "indexing_state",
            "lastCrawlTime": "last_crawl_time",
            "pageFetchState": "page_fetch_state",
            "googleCanonical": "google_canonical",
            "userCanonical": "user_canonical",
            "crawledAs": "crawled_as",
        }
        result: dict[str, object] = {"inspection_url": target}
        for provider_key, output_key in allowed.items():
            value = index.get(provider_key)
            if isinstance(value, (str, bool, int, float)) or value is None:
                result[output_key] = value
        return result

    def search_analytics(
        self,
        site_url: str,
        *,
        start_date: str,
        end_date: str,
        dimensions: list[str] | tuple[str, ...] | None = None,
        search_type: str = "WEB",
        data_state: str = "FINAL",
        aggregation_type: str = "AUTO",
        row_limit: int = 1000,
        start_row: int = 0,
    ) -> dict[str, object]:
        site = canonical_site_url(site_url)
        query = search_analytics_query(
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            search_type=search_type,
            data_state=data_state,
            aggregation_type=aggregation_type,
            row_limit=row_limit,
            start_row=start_row,
        )
        payload = self._api.request_json(
            "POST",
            f"{WEBMASTERS_BASE}/sites/{quote(site, safe='')}/searchAnalytics/query",
            body=query,
            read_only=True,
        )
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise AdapterError("provider_rejected", "failed", 14, "The Search Analytics response had an unsupported shape.")
        provider_rows = payload.get("rows", [])
        if not isinstance(provider_rows, list):
            raise AdapterError("provider_rejected", "failed", 14, "The Search Analytics response rows were not a list.")

        normalized_rows: list[dict[str, object]] = []
        expected_keys = len(query["dimensions"])
        for provider_row in provider_rows:
            if not isinstance(provider_row, dict):
                raise AdapterError("provider_rejected", "failed", 14, "A Search Analytics row had an unsupported shape.")
            keys = provider_row.get("keys", []) if expected_keys == 0 else provider_row.get("keys")
            if (
                not isinstance(keys, list)
                or len(keys) != expected_keys
                or any(not isinstance(value, str) for value in keys)
            ):
                raise AdapterError("provider_rejected", "failed", 14, "A Search Analytics row contained invalid dimension keys.")
            normalized_rows.append(
                {
                    "keys": list(keys),
                    "clicks": _search_metric(provider_row, "clicks"),
                    "impressions": _search_metric(provider_row, "impressions"),
                    "ctr": _search_metric(provider_row, "ctr"),
                    "position": _search_metric(provider_row, "position"),
                }
            )

        provider_aggregation = payload.get("responseAggregationType")
        response_aggregation = None
        if provider_aggregation is not None:
            if not isinstance(provider_aggregation, str):
                raise AdapterError("provider_rejected", "failed", 14, "The Search Analytics response used an unsupported aggregation type.")
            response_aggregation = RESPONSE_AGGREGATION_ALIASES.get(provider_aggregation)
            if response_aggregation is None:
                raise AdapterError("provider_rejected", "failed", 14, "The Search Analytics response used an unsupported aggregation type.")
        return {
            "site_url": site,
            "start_date": query["startDate"],
            "end_date": query["endDate"],
            "dimensions": query["dimensions"],
            "search_type": query["type"],
            "data_state": query["dataState"],
            "aggregation_type": query["aggregationType"],
            "row_limit": query["rowLimit"],
            "start_row": query["startRow"],
            "row_count": len(normalized_rows),
            "row_limit_reached": len(normalized_rows) == row_limit,
            "response_aggregation_type": response_aggregation,
            "rows": normalized_rows,
        }


def sitemap_target(site_url: str, sitemap_url: str, *, operation: str) -> tuple[dict[str, object], str]:
    site = canonical_site_url(site_url)
    sitemap = canonical_target_url(sitemap_url)
    if not property_contains(site, sitemap):
        raise AdapterError("target_mismatch", "blocked", 12, "The sitemap URL is outside the exact Search Console property scope.")
    digest = target_fingerprint(
        provider="gsc",
        resource_type="sitemap",
        resource_name=site,
        operation=operation,
        site_url=site,
        sitemap_url=sitemap,
    )
    return {
        "resource_type": "gsc_sitemap",
        "resource_name": site,
        "site_url": site,
        "sitemap_url": sitemap,
        "target_fingerprint": digest,
    }, digest
