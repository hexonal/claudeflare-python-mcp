"""
Workers、AI 与 Analytics 相关 Cloudflare API 方法 Mixin。
Workers, AI and Analytics related Cloudflare API methods mixin.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from .cf_handler_base import CloudflareBase, WorkerData, _CF_API_BASE

# Cloudflare GraphQL Analytics API 查询（最近 24 小时，按小时分组）
_ANALYTICS_QUERY = """
query($zoneTag: String!, $start: Time!, $end: Time!) {
  viewer {
    zones(filter: {zoneTag: $zoneTag}) {
      httpRequests1hGroups(
        limit: 24
        orderBy: [datetimeHour_ASC]
        filter: {datetimeHour_geq: $start, datetimeHour_lt: $end}
      ) {
        sum {
          requests
          cachedRequests
          bytes
          cachedBytes
          threats
          pageViews
        }
      }
    }
  }
}
"""


class WorkersMixin(CloudflareBase):
    """
    Workers、AI 和 Analytics 操作 Mixin。
    Workers, AI and Analytics operations mixin.
    """

    # -- Analytics --

    async def get_zone_analytics(self, zone_id: str) -> dict[str, object]:
        """
        获取 Zone 最近 24 小时的流量分析（使用 Cloudflare GraphQL Analytics API）。
        Get zone traffic analytics for the last 24 hours via Cloudflare GraphQL Analytics API.
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=24)
        variables = {
            "zoneTag": zone_id,
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{_CF_API_BASE}/graphql",
                headers=self._get_auth_headers(),
                json={"query": _ANALYTICS_QUERY, "variables": variables},
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
        gql_data = data.get("data", {})
        if not isinstance(gql_data, dict):
            return {}
        viewer = gql_data.get("viewer", {})
        if not isinstance(viewer, dict):
            return {}
        zone_list = viewer.get("zones", [])
        if not isinstance(zone_list, list) or not zone_list:
            return {}
        first = zone_list[0]
        if not isinstance(first, dict):
            return {}
        groups = first.get("httpRequests1hGroups", [])
        if not isinstance(groups, list):
            return {}
        return self._aggregate_analytics(groups)

    def _aggregate_analytics(self, groups: list[object]) -> dict[str, object]:
        """
        聚合 GraphQL Analytics 小时分组数据为汇总统计。
        Aggregate GraphQL Analytics hourly groups into summary statistics.
        """
        req = cached_req = bw = cached_bw = threats = pv = 0
        for g in groups:
            if not isinstance(g, dict):
                continue
            s = g.get("sum", {})
            if not isinstance(s, dict):
                continue
            req += int(s.get("requests", 0))
            cached_req += int(s.get("cachedRequests", 0))
            bw += int(s.get("bytes", 0))
            cached_bw += int(s.get("cachedBytes", 0))
            threats += int(s.get("threats", 0))
            pv += int(s.get("pageViews", 0))
        return {
            "requests": {"total": req, "cached": cached_req, "uncached": req - cached_req},
            "bandwidth": {"total": bw, "cached": cached_bw, "uncached": bw - cached_bw},
            "threats": {"total": threats},
            "pageviews": {"total": pv},
        }

    # -- AI (Workers AI) --

    async def list_ai_models(self, account_id: str) -> list[dict[str, object]]:
        """
        列出账户下可用的 Workers AI 模型。
        List available Workers AI models for an account.
        """
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{_CF_API_BASE}/accounts/{account_id}/ai/models/search",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result = data.get("result", [])
            if not isinstance(result, list):
                return []
            return [
                {
                    "id": str(m.get("id", "")),
                    "name": str(m.get("name", "")),
                    "task": m.get("task", {}),
                }
                for m in result
                if isinstance(m, dict)
            ]

    async def run_ai(self, account_id: str, model_name: str, prompt: str) -> dict[str, object]:
        """
        调用 Workers AI 模型执行推理（对话格式）。
        Run inference on a Workers AI model (chat format).
        """
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(
                f"{_CF_API_BASE}/accounts/{account_id}/ai/run/{model_name}",
                headers=self._get_auth_headers(),
                json={"messages": [{"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result = data.get("result", {})
            if not isinstance(result, dict):
                return {"response": str(result)}
            return result

    # -- Workers --

    async def list_workers(self, account_id: str) -> list[WorkerData]:
        """
        列出账户下的所有 Workers 脚本。
        List all Workers scripts for an account.
        """
        async with self._get_client() as client:
            page = await client.workers.scripts.list(account_id=account_id)
            script_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
            return [
                {
                    "id": s.id,  # type: ignore[attr-defined]
                    "created_on": str(s.created_on),  # type: ignore[attr-defined]
                    "modified_on": str(s.modified_on),  # type: ignore[attr-defined]
                    "etag": s.etag,  # type: ignore[attr-defined]
                }
                for s in script_items
            ]

    async def list_worker_routes(self, zone_id: str) -> list[dict[str, object]]:
        """
        列出 Zone 的 Worker 路由规则。
        List Worker routes for a zone.
        """
        async with self._get_client() as client:
            page = await client.workers.routes.list(zone_id=zone_id)
            route_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
            return [
                {
                    "id": r.id,  # type: ignore[attr-defined]
                    "pattern": r.pattern,  # type: ignore[attr-defined]
                    "script": r.script,  # type: ignore[attr-defined]
                }
                for r in route_items
            ]

    async def get_worker(self, account_id: str, script_name: str) -> WorkerData:
        """
        获取指定 Worker 脚本的元数据（通过 httpx 调用脚本列表接口并过滤）。
        Get Worker script metadata via httpx (lists scripts and filters by name).

        SDK 的 workers.scripts.get() 返回脚本内容而非元数据，改用 httpx。
        SDK workers.scripts.get() returns script content, not metadata; uses httpx.
        """
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{_CF_API_BASE}/accounts/{account_id}/workers/scripts",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result = data.get("result", [])
            if not isinstance(result, list):
                return {}
            for script in result:
                if isinstance(script, dict) and script.get("id") == script_name:
                    return {
                        "id": str(script.get("id", "")),
                        "created_on": str(script.get("created_on", "")),
                        "modified_on": str(script.get("modified_on", "")),
                        "etag": str(script.get("etag", "")),
                    }
            raise ValueError(f"Worker 脚本 {script_name} 不存在")
