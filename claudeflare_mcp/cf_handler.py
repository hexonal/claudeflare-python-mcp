"""
Cloudflare API 处理器模块。
Cloudflare API handler module.
"""

import os
from datetime import datetime, timedelta, timezone

import cloudflare
import httpx

# Python 3.12+ type 关键字定义类型别名
type ZoneData = dict[str, object]
type DnsRecordData = dict[str, object]
type SettingsData = dict[str, object]
type WorkerData = dict[str, object]

_CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
_CF_API_KEY = os.environ.get("CF_API_KEY", "")
_CF_API_EMAIL = os.environ.get("CF_API_EMAIL", "")

_CF_API_BASE = "https://api.cloudflare.com/client/v4"

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



class CloudflareHandler:
    """
    Cloudflare API 处理器，封装所有 SDK 调用。
    Cloudflare API handler that wraps all SDK calls.
    """

    # Zone Settings 过滤键集合（作为类常量供方法引用）
    _CACHE_KEYS: frozenset[str] = frozenset(
        {"cache_level", "browser_cache_ttl", "always_online", "development_mode", "edge_cache_ttl"}
    )
    _SPEED_KEYS: frozenset[str] = frozenset(
        {
            "brotli",
            "early_hints",
            "h2_prioritization",
            "minify",
            "mirage",
            "polish",
            "prefetch_preload",
            "rocket_loader",
            "http2",
            "http3",
        }
    )
    _SECURITY_KEYS: frozenset[str] = frozenset(
        {
            "security_level",
            "browser_check",
            "challenge_ttl",
            "hotlink_protection",
            "privacy_pass",
            "waf",
        }
    )

    def _get_client(self) -> cloudflare.AsyncCloudflare:
        """
        创建 Cloudflare 异步客户端（支持 API Token 和 Global API Key 双认证模式）。
        Create async Cloudflare client (supports API Token and Global API Key auth modes).
        """
        if _CF_API_TOKEN:
            return cloudflare.AsyncCloudflare(api_token=_CF_API_TOKEN)
        if _CF_API_KEY and _CF_API_EMAIL:
            return cloudflare.AsyncCloudflare(api_email=_CF_API_EMAIL, api_key=_CF_API_KEY)
        raise ValueError("需要设置 CF_API_TOKEN 或 CF_API_KEY + CF_API_EMAIL，请检查 MCP 配置的 env 字段")

    def _get_auth_headers(self) -> dict[str, str]:
        """
        获取 HTTP 请求认证头（支持 API Token 和 Global API Key 双模式）。
        Get HTTP authentication headers (supports API Token and Global API Key modes).
        """
        if _CF_API_TOKEN:
            return {"Authorization": f"Bearer {_CF_API_TOKEN}"}
        if _CF_API_KEY and _CF_API_EMAIL:
            return {"X-Auth-Email": _CF_API_EMAIL, "X-Auth-Key": _CF_API_KEY}
        raise ValueError("需要设置 CF_API_TOKEN 或 CF_API_KEY + CF_API_EMAIL，请检查 MCP 配置的 env 字段")

    async def list_zones(self) -> list[ZoneData]:
        """
        列出账户下所有 Zone（域名）。
        List all Zones (domains) in the account.
        """
        async with self._get_client() as client:
            page = await client.zones.list()
            # 真实 SDK 返回 AsyncV4PagePaginationArray（Pydantic 模型），需通过 .result 取列表
            # Mock 测试返回普通 list，直接使用
            zone_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            result: list[ZoneData] = []
            for z in zone_items:
                result.append(
                    {
                        "id": z.id,  # type: ignore[attr-defined]
                        "name": z.name,  # type: ignore[attr-defined]
                        "status": z.status,  # type: ignore[attr-defined]
                        "plan": z.plan.name if z.plan else None,  # type: ignore[attr-defined]
                    }
                )
            return result

    async def list_dns_records(self, zone_id: str) -> list[DnsRecordData]:
        """
        列出指定 Zone 的所有 DNS 记录。
        List all DNS records for a zone.
        """
        async with self._get_client() as client:
            page = await client.dns.records.list(zone_id=zone_id)
            record_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            result: list[DnsRecordData] = []
            for r in record_items:
                result.append(
                    {
                        "id": r.id,  # type: ignore[attr-defined]
                        "type": r.type,  # type: ignore[attr-defined]
                        "name": r.name,  # type: ignore[attr-defined]
                        "content": r.content,  # type: ignore[attr-defined]
                        "ttl": r.ttl,  # type: ignore[attr-defined]
                        "proxied": r.proxied,  # type: ignore[attr-defined]
                    }
                )
            return result

    async def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 1,
        proxied: bool = False,
    ) -> DnsRecordData:
        """
        创建 DNS 记录。
        Create a DNS record.
        """
        async with self._get_client() as client:
            record = await client.dns.records.create(  # type: ignore[call-overload]
                zone_id=zone_id,
                type=record_type,  # pyright: ignore[reportArgumentType]
                name=name,
                content=content,
                ttl=ttl,
                proxied=proxied,
            )
            return {
                "id": record.id,
                "type": record.type,
                "name": record.name,
                "content": record.content,
                "proxied": record.proxied,
            }

    async def update_dns_record(
        self,
        zone_id: str,
        record_id: str,
        content: str,
        ttl: int = 1,
        proxied: bool | None = None,
    ) -> DnsRecordData:
        """
        更新 DNS 记录内容（先获取现有记录保留 name/type，再 PATCH 更新）。
        Update DNS record content (fetches existing record to preserve name/type, then PATCH).
        """
        async with self._get_client() as client:
            # 先获取现有记录以保留 name、type 和 proxied
            existing = await client.dns.records.get(record_id, zone_id=zone_id)
            # proxied 为 None 时保留现有值，否则使用传入值
            effective_proxied = proxied if proxied is not None else existing.proxied  # type: ignore[union-attr]
            record = await client.dns.records.edit(
                record_id,
                zone_id=zone_id,
                name=existing.name,  # type: ignore[union-attr]
                type=existing.type,  # type: ignore[union-attr, arg-type]
                content=content,
                ttl=ttl,
                proxied=effective_proxied,
            )
            return {
                "id": record.id,  # type: ignore[union-attr]
                "type": record.type,  # type: ignore[union-attr]
                "name": record.name,  # type: ignore[union-attr]
                "content": record.content,  # type: ignore[union-attr]
                "proxied": record.proxied,  # type: ignore[union-attr]
            }

    async def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """
        删除 DNS 记录。
        Delete a DNS record.
        """
        async with self._get_client() as client:
            await client.dns.records.delete(record_id, zone_id=zone_id)
            return True

    async def get_zone_settings(self, zone_id: str) -> dict[str, object]:
        """
        获取 Zone 的安全和性能设置（直接调用 Cloudflare REST API）。
        Get zone security and performance settings (via direct REST API call).

        SDK v4 移除了 zones.settings.list()，改用 httpx 直接调用端点。
        SDK v4 removed zones.settings.list(); calls the endpoint directly via httpx.
        """
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{_CF_API_BASE}/zones/{zone_id}/settings",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result = data.get("result", [])
            if not isinstance(result, list):
                return {}
            return {
                str(item["id"]): item["value"]
                for item in result
                if isinstance(item, dict) and "id" in item and item.get("value") is not None
            }

    async def _get_zone_settings_filtered(
        self, zone_id: str, keys: frozenset[str]
    ) -> dict[str, object]:
        """
        获取 Zone Settings 并按键名过滤。
        Fetch zone settings and filter by key names.
        """
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{_CF_API_BASE}/zones/{zone_id}/settings",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result = data.get("result", [])
            if not isinstance(result, list):
                return {}
            return {
                str(item["id"]): item["value"]
                for item in result
                if isinstance(item, dict)
                and item.get("id") in keys
                and item.get("value") is not None
            }

    # ── Caching ──────────────────────────────────────────────────────────────

    async def purge_cache(
        self,
        zone_id: str,
        files: str = "",
        tags: str = "",
        purge_everything: bool = False,
    ) -> dict[str, object]:
        """
        清除 Zone 缓存（全部清除、按 URL、或按 Cache-Tag）。
        Purge zone cache (everything, by URLs, or by cache tags).
        """
        async with self._get_client() as client:
            if purge_everything:
                await client.cache.purge(zone_id=zone_id, purge_everything=True)
            elif files:
                file_list = [f.strip() for f in files.split(",") if f.strip()]
                await client.cache.purge(zone_id=zone_id, files=file_list)
            elif tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                await client.cache.purge(zone_id=zone_id, tags=tag_list)
            else:
                raise ValueError("必须指定 purge_everything=True、files 或 tags 之一")
            return {"purged": True, "zone_id": zone_id}

    async def get_cache_settings(self, zone_id: str) -> SettingsData:
        """
        获取 Zone 的缓存相关配置。
        Get cache-related settings for a zone.
        """
        return await self._get_zone_settings_filtered(zone_id, self._CACHE_KEYS)

    # ── Speed ─────────────────────────────────────────────────────────────────

    async def get_speed_settings(self, zone_id: str) -> SettingsData:
        """
        获取 Zone 的性能优化配置（Brotli、HTTP/2 等）。
        Get speed optimization settings for a zone (Brotli, HTTP/2, etc.).
        """
        return await self._get_zone_settings_filtered(zone_id, self._SPEED_KEYS)

    # ── Security ─────────────────────────────────────────────────────────────

    async def list_firewall_rules(self, zone_id: str) -> list[dict[str, object]]:
        """
        列出 Zone 的防火墙访问规则。
        List firewall access rules for a zone.
        """
        async with self._get_client() as client:
            page = await client.firewall.access_rules.list(zone_id=zone_id)
            rule_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            result: list[dict[str, object]] = []
            for r in rule_items:
                result.append(
                    {
                        "id": r.id,  # type: ignore[attr-defined]
                        "mode": r.mode,  # type: ignore[attr-defined]
                        "notes": r.notes,  # type: ignore[attr-defined]
                        "configuration": r.configuration,  # type: ignore[attr-defined]
                    }
                )
            return result

    async def get_security_settings(self, zone_id: str) -> SettingsData:
        """
        获取 Zone 的安全配置（安全级别、WAF 等）。
        Get security settings for a zone (security level, WAF, etc.).
        """
        return await self._get_zone_settings_filtered(zone_id, self._SECURITY_KEYS)

    # ── SSL/TLS ───────────────────────────────────────────────────────────────

    async def get_ssl_settings(self, zone_id: str) -> dict[str, object]:
        """
        获取 Zone 的 SSL/TLS 通用设置。
        Get SSL/TLS universal settings for a zone.
        """
        async with self._get_client() as client:
            ssl = await client.ssl.universal.settings.get(zone_id=zone_id)
            return {
                "enabled": ssl.enabled,  # type: ignore[union-attr]
                "certificate_authority": ssl.certificate_authority,  # type: ignore[union-attr]
            }

    async def list_ssl_certificates(self, zone_id: str) -> list[dict[str, object]]:
        """
        列出 Zone 的 SSL 证书包。
        List SSL certificate packs for a zone.
        """
        async with self._get_client() as client:
            page = await client.ssl.certificate_packs.list(zone_id=zone_id)
            cert_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            result: list[dict[str, object]] = []
            for c in cert_items:
                # 兼容 SDK 模型对象和原始 dict（不同端点返回类型不一致）
                if isinstance(c, dict):
                    result.append(
                        {
                            "id": c.get("id"),
                            "type": c.get("type"),
                            "status": c.get("status"),
                            "hosts": c.get("hosts"),
                        }
                    )
                else:
                    result.append(
                        {
                            "id": c.id,  # type: ignore[attr-defined]
                            "type": c.type,  # type: ignore[attr-defined]
                            "status": c.status,  # type: ignore[attr-defined]
                            "hosts": c.hosts,  # type: ignore[attr-defined]
                        }
                    )
            return result

    # ── Custom Hostnames ──────────────────────────────────────────────────────

    async def list_custom_hostnames(self, zone_id: str) -> list[dict[str, object]]:
        """
        列出 Zone 的自定义主机名。
        List custom hostnames for a zone.
        """
        async with self._get_client() as client:
            page = await client.custom_hostnames.list(zone_id=zone_id)
            hostname_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            return [
                {
                    "id": h.id,  # type: ignore[attr-defined]
                    "hostname": h.hostname,  # type: ignore[attr-defined]
                    "status": h.status,  # type: ignore[attr-defined]
                }
                for h in hostname_items
            ]

    async def create_custom_hostname(self, zone_id: str, hostname: str) -> dict[str, object]:
        """
        创建自定义主机名（默认使用 HTTP DV 证书）。
        Create a custom hostname (defaults to HTTP DV certificate).
        """
        async with self._get_client() as client:
            result = await client.custom_hostnames.create(
                zone_id=zone_id,
                hostname=hostname,
                ssl={"method": "http", "type": "dv"},
            )
            return {
                "id": result.id,  # type: ignore[union-attr]
                "hostname": result.hostname,  # type: ignore[union-attr]
                "status": result.status,  # type: ignore[union-attr]
            }

    # ── Email Routing ─────────────────────────────────────────────────────────

    async def get_email_routing(self, zone_id: str) -> dict[str, object]:
        """
        获取 Zone 的邮件路由设置。
        Get email routing settings for a zone.
        """
        async with self._get_client() as client:
            routing = await client.email_routing.get(zone_id=zone_id)
            return {
                "id": routing.id,  # type: ignore[union-attr]
                "name": routing.name,  # type: ignore[union-attr]
                "enabled": routing.enabled,  # type: ignore[union-attr]
                "status": routing.status,  # type: ignore[union-attr]
            }

    async def list_email_routing_rules(self, zone_id: str) -> list[dict[str, object]]:
        """
        列出 Zone 的邮件路由规则。
        List email routing rules for a zone.
        """
        async with self._get_client() as client:
            page = await client.email_routing.rules.list(zone_id=zone_id)
            rule_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            return [
                {
                    "id": r.id,  # type: ignore[attr-defined]
                    "name": r.name,  # type: ignore[attr-defined]
                    "enabled": r.enabled,  # type: ignore[attr-defined]
                    "priority": r.priority,  # type: ignore[attr-defined]
                }
                for r in rule_items
            ]

    # ── DNS 扩展 ──────────────────────────────────────────────────────────────

    async def get_dnssec(self, zone_id: str) -> dict[str, object]:
        """
        获取 Zone 的 DNSSEC 状态。
        Get DNSSEC status for a zone.
        """
        async with self._get_client() as client:
            dnssec = await client.dns.dnssec.get(zone_id=zone_id)
            return {
                "status": dnssec.status,  # type: ignore[union-attr]
                "ds": dnssec.ds,  # type: ignore[union-attr]
                "algorithm": dnssec.algorithm,  # type: ignore[union-attr]
                "digest_type": dnssec.digest_type,  # type: ignore[union-attr]
            }

    async def get_dns_settings(self, zone_id: str) -> dict[str, object]:
        """
        获取 Zone 的 DNS 设置（基础架构配置）。
        Get DNS settings for a zone (infrastructure configuration).

        SDK v4 的 dns.settings 无 get() 方法，改用 httpx 直接调用。
        SDK v4 dns.settings lacks get(); calls the endpoint directly via httpx.
        """
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{_CF_API_BASE}/zones/{zone_id}/dns_settings",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result = data.get("result", {})
            if not isinstance(result, dict):
                return {}
            return result

    # ── Analytics ─────────────────────────────────────────────────────────────

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

    # ── AI (Workers AI) ───────────────────────────────────────────────────────

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

    # ── Workers ───────────────────────────────────────────────────────────────

    async def list_workers(self, account_id: str) -> list[WorkerData]:
        """
        列出账户下的所有 Workers 脚本。
        List all Workers scripts for an account.
        """
        async with self._get_client() as client:
            page = await client.workers.scripts.list(account_id=account_id)
            script_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
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
            route_items: list[object] = page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
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
