"""
Cloudflare API 处理器模块。
Cloudflare API handler module.
"""

import os
from typing import TypedDict

import cloudflare
import httpx

from .cf_handler_dns import DnsMixin
from .cf_handler_ssl import SslMixin
from .cf_handler_workers import WorkersMixin

# Python 3.12+ type 关键字定义类型别名
type ZoneData = dict[str, object]
type DnsRecordData = dict[str, object]
type SettingsData = dict[str, object]
type WorkerData = dict[str, object]


class CreateDnsRecordParams(TypedDict):
    """
    创建 DNS 记录的参数结构体。
    Parameters for creating a DNS record.
    """

    record_type: str
    name: str
    content: str
    ttl: int
    proxied: bool


class UpdateDnsRecordParams(TypedDict):
    """
    更新 DNS 记录的参数结构体。
    Parameters for updating a DNS record.
    """

    content: str
    ttl: int
    proxied: bool | None

_CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
_CF_API_KEY = os.environ.get("CF_API_KEY", "")
_CF_API_EMAIL = os.environ.get("CF_API_EMAIL", "")

_CF_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareHandler(DnsMixin, SslMixin, WorkersMixin):
    """
    Cloudflare API 处理器，封装所有 SDK 调用。
    Cloudflare API handler that wraps all SDK calls.

    通过 Mixin 模式组合 DNS、SSL 和 Workers/AI/Analytics 功能。
    Composes DNS, SSL and Workers/AI/Analytics features via Mixin pattern.
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
        raise ValueError(
            "需要设置 CF_API_TOKEN 或 CF_API_KEY + CF_API_EMAIL，请检查 MCP 配置的 env 字段"
        )

    def _get_auth_headers(self) -> dict[str, str]:
        """
        获取 HTTP 请求认证头（支持 API Token 和 Global API Key 双模式）。
        Get HTTP authentication headers (supports API Token and Global API Key modes).
        """
        if _CF_API_TOKEN:
            return {"Authorization": f"Bearer {_CF_API_TOKEN}"}
        if _CF_API_KEY and _CF_API_EMAIL:
            return {"X-Auth-Email": _CF_API_EMAIL, "X-Auth-Key": _CF_API_KEY}
        raise ValueError(
            "需要设置 CF_API_TOKEN 或 CF_API_KEY + CF_API_EMAIL，请检查 MCP 配置的 env 字段"
        )

    async def list_zones(self) -> list[ZoneData]:
        """
        列出账户下所有 Zone（域名）。
        List all Zones (domains) in the account.
        """
        async with self._get_client() as client:
            page = await client.zones.list()
            # 真实 SDK 返回 AsyncV4PagePaginationArray（Pydantic 模型），需通过 .result 取列表
            # Mock 测试返回普通 list，直接使用
            zone_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
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
            rule_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
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
            rule_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
            return [
                {
                    "id": r.id,  # type: ignore[attr-defined]
                    "name": r.name,  # type: ignore[attr-defined]
                    "enabled": r.enabled,  # type: ignore[attr-defined]
                    "priority": r.priority,  # type: ignore[attr-defined]
                }
                for r in rule_items
            ]
