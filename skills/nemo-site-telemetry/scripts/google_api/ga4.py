"""Restricted GA4 Admin/Data API read and create-only surface."""

from __future__ import annotations

import re
from urllib.parse import quote, urlencode

from .http import GoogleApiClient
from .output import AdapterError
from .plans import canonical_origin, target_fingerprint


ADMIN_BASE = "https://analyticsadmin.googleapis.com/v1beta"
DATA_BASE = "https://analyticsdata.googleapis.com/v1beta"
ALLOWED_REALTIME_METRICS = frozenset({"activeUsers", "eventCount", "screenPageViews"})
_ID = re.compile(r"^[0-9]+$")


def account_name(value: str) -> str:
    raw = value.removeprefix("accounts/")
    if not _ID.fullmatch(raw):
        raise AdapterError("invalid_input", "blocked", 12, "Provide one exact numeric GA4 account ID.")
    return f"accounts/{raw}"


def property_name(value: str) -> str:
    raw = value.removeprefix("properties/")
    if not _ID.fullmatch(raw):
        raise AdapterError("invalid_input", "blocked", 12, "Provide one exact numeric GA4 property ID.")
    return f"properties/{raw}"


def _property_summary(item: object) -> dict[str, object] | None:
    if not isinstance(item, dict) or not isinstance(item.get("name"), str):
        return None
    return {
        "name": item["name"],
        "parent": item.get("parent") if isinstance(item.get("parent"), str) else None,
        "display_name": item.get("displayName") if isinstance(item.get("displayName"), str) else None,
        "time_zone": item.get("timeZone") if isinstance(item.get("timeZone"), str) else None,
        "currency_code": item.get("currencyCode") if isinstance(item.get("currencyCode"), str) else None,
        "create_time": item.get("createTime") if isinstance(item.get("createTime"), str) else None,
    }


def _stream_summary(item: object, *, strict_web_uri: bool = False) -> dict[str, object] | None:
    if not isinstance(item, dict) or not isinstance(item.get("name"), str):
        return None
    stream_type = item.get("type") if isinstance(item.get("type"), str) else "unknown"
    web_data = item.get("webStreamData") if isinstance(item.get("webStreamData"), dict) else {}
    default_uri = web_data.get("defaultUri") if isinstance(web_data.get("defaultUri"), str) else None
    normalized_uri = None
    if default_uri:
        try:
            normalized_uri = canonical_origin(default_uri)
        except AdapterError:
            if strict_web_uri and stream_type == "WEB_DATA_STREAM":
                raise AdapterError(
                    "provider_rejected",
                    "failed",
                    14,
                    "A provider Web data stream has an invalid default URI; stop before any create.",
                ) from None
    if strict_web_uri and stream_type == "WEB_DATA_STREAM" and normalized_uri is None:
        raise AdapterError(
            "provider_rejected",
            "failed",
            14,
            "A provider Web data stream lacks a valid default URI; stop before any create.",
        )
    return {
        "name": item["name"],
        "type": stream_type,
        "display_name": item.get("displayName") if isinstance(item.get("displayName"), str) else None,
        "default_uri": normalized_uri,
        "measurement_id": web_data.get("measurementId") if isinstance(web_data.get("measurementId"), str) else None,
        "create_time": item.get("createTime") if isinstance(item.get("createTime"), str) else None,
    }


class GA4Client:
    def __init__(self, api: GoogleApiClient) -> None:
        self._api = api

    def list_account_summaries(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        page_token: str | None = None
        for _ in range(10):
            query = urlencode({"pageSize": 200, **({"pageToken": page_token} if page_token else {})})
            payload = self._api.request_json("GET", f"{ADMIN_BASE}/accountSummaries?{query}")
            if not isinstance(payload, dict):
                break
            summaries = payload.get("accountSummaries", [])
            if isinstance(summaries, list):
                for item in summaries:
                    if not isinstance(item, dict) or not isinstance(item.get("account"), str):
                        continue
                    properties: list[dict[str, object]] = []
                    raw_properties = item.get("propertySummaries", [])
                    if isinstance(raw_properties, list):
                        for prop in raw_properties:
                            if isinstance(prop, dict) and isinstance(prop.get("property"), str):
                                properties.append(
                                    {
                                        "property": prop["property"],
                                        "display_name": prop.get("displayName") if isinstance(prop.get("displayName"), str) else None,
                                    }
                                )
                    items.append(
                        {
                            "account": item["account"],
                            "display_name": item.get("displayName") if isinstance(item.get("displayName"), str) else None,
                            "properties": properties,
                        }
                    )
            next_token = payload.get("nextPageToken")
            if not isinstance(next_token, str) or not next_token:
                break
            page_token = next_token
        return items

    def get_property(self, property_id: str, *, allow_not_found: bool = False) -> dict[str, object] | None:
        name = property_name(property_id)
        payload = self._api.request_json("GET", f"{ADMIN_BASE}/{quote(name, safe='/')}", allow_not_found=allow_not_found)
        if payload is None:
            return None
        summary = _property_summary(payload)
        if summary is None or summary["name"] != name:
            raise AdapterError("target_mismatch", "blocked", 12, "The provider returned a different GA4 property.")
        return summary

    def list_properties(self, account_id: str) -> list[dict[str, object]]:
        account = account_name(account_id)
        items: list[dict[str, object]] = []
        page_token: str | None = None
        for _ in range(10):
            params: dict[str, object] = {"filter": f"parent:{account}", "pageSize": 200}
            if page_token:
                params["pageToken"] = page_token
            payload = self._api.request_json("GET", f"{ADMIN_BASE}/properties?{urlencode(params)}")
            if not isinstance(payload, dict):
                break
            properties = payload.get("properties", [])
            if isinstance(properties, list):
                items.extend(summary for item in properties if (summary := _property_summary(item)) is not None)
            next_token = payload.get("nextPageToken")
            if not isinstance(next_token, str) or not next_token:
                break
            page_token = next_token
        return items

    def list_web_streams(self, property_id: str) -> list[dict[str, object]]:
        name = property_name(property_id)
        items: list[dict[str, object]] = []
        page_token: str | None = None
        for _ in range(10):
            params: dict[str, object] = {"pageSize": 200}
            if page_token:
                params["pageToken"] = page_token
            payload = self._api.request_json("GET", f"{ADMIN_BASE}/{quote(name, safe='/')}/dataStreams?{urlencode(params)}")
            if not isinstance(payload, dict):
                break
            streams = payload.get("dataStreams", [])
            if isinstance(streams, list):
                for item in streams:
                    summary = _stream_summary(item, strict_web_uri=True)
                    if summary is not None and summary["type"] == "WEB_DATA_STREAM":
                        items.append(summary)
            next_token = payload.get("nextPageToken")
            if not isinstance(next_token, str) or not next_token:
                break
            page_token = next_token
        return items

    def realtime(self, property_id: str, metric: str) -> dict[str, object]:
        name = property_name(property_id)
        if metric not in ALLOWED_REALTIME_METRICS:
            raise AdapterError("invalid_input", "blocked", 12, "Choose a telemetry-verification metric from the fixed allowlist.")
        payload = self._api.request_json(
            "POST",
            f"{DATA_BASE}/{quote(name, safe='/')}:runRealtimeReport",
            body={"metrics": [{"name": metric}], "limit": "10"},
            read_only=True,
        )
        if not isinstance(payload, dict):
            return {"metric": metric, "row_count": 0, "values": []}
        values: list[str] = []
        rows = payload.get("rows", [])
        if isinstance(rows, list):
            for row in rows[:10]:
                if not isinstance(row, dict):
                    continue
                metrics = row.get("metricValues", [])
                if isinstance(metrics, list) and metrics and isinstance(metrics[0], dict) and isinstance(metrics[0].get("value"), str):
                    values.append(metrics[0]["value"])
        return {"metric": metric, "row_count": len(values), "values": values}

    def create_property(self, account_id: str, *, display_name: str, time_zone: str, currency_code: str) -> dict[str, object]:
        account = account_name(account_id)
        payload = self._api.request_json(
            "POST",
            f"{ADMIN_BASE}/properties",
            body={"parent": account, "displayName": display_name, "timeZone": time_zone, "currencyCode": currency_code},
        )
        summary = _property_summary(payload)
        if summary is None:
            raise AdapterError("ambiguous_write", "pending", 13, "Read back the account properties; do not replay the create request.", retryable=False)
        return summary

    def create_web_stream(self, property_id: str, *, display_name: str, production_origin: str) -> dict[str, object]:
        name = property_name(property_id)
        origin = canonical_origin(production_origin)
        payload = self._api.request_json(
            "POST",
            f"{ADMIN_BASE}/{quote(name, safe='/')}/dataStreams",
            body={"type": "WEB_DATA_STREAM", "displayName": display_name, "webStreamData": {"defaultUri": origin}},
        )
        summary = _stream_summary(payload)
        if summary is None or summary.get("type") != "WEB_DATA_STREAM" or summary.get("default_uri") != origin:
            raise AdapterError("ambiguous_write", "pending", 13, "Read back the exact property streams; do not replay the create request.", retryable=False)
        return summary

    def find_origin_matches(self, account_id: str, production_origin: str) -> list[dict[str, object]]:
        account = account_name(account_id)
        origin = canonical_origin(production_origin)
        matches: list[dict[str, object]] = []
        for prop in self.list_properties(account):
            name = prop.get("name")
            if not isinstance(name, str):
                continue
            for stream in self.list_web_streams(name):
                if stream.get("default_uri") == origin:
                    matches.append({"account": account, "property": prop, "stream": stream})
        return matches


def ga4_target(
    *,
    account_id: str,
    production_origin: str,
    operation: str,
    property_id: str | None = None,
) -> tuple[dict[str, object], str]:
    account = account_name(account_id)
    origin = canonical_origin(production_origin)
    prop = property_name(property_id) if property_id else None
    resource_name = prop or account
    digest = target_fingerprint(
        provider="ga4",
        resource_type="web_stream",
        resource_name=resource_name,
        operation=operation,
        canonical_origin_value=origin,
        account_name=account,
        property_name=prop,
    )
    return {
        "resource_type": "ga4_web_stream",
        "resource_name": resource_name,
        "canonical_origin": origin,
        "target_fingerprint": digest,
    }, digest
