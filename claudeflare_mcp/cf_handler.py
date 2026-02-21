"""
Cloudflare API 处理器模块。
Cloudflare API handler module.
"""

import os

import cloudflare

# 公开 re-export，供外部模块（__init__.py、测试等）直接从此处导入
from .cf_handler_base import CreateDnsRecordParams, UpdateDnsRecordParams

__all__ = ["CloudflareHandler", "CreateDnsRecordParams", "UpdateDnsRecordParams"]
from .cf_handler_dns import DnsMixin
from .cf_handler_ssl import SslMixin
from .cf_handler_workers import WorkersMixin
from .cf_handler_zone import ZoneMixin

_CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
_CF_API_KEY = os.environ.get("CF_API_KEY", "")
_CF_API_EMAIL = os.environ.get("CF_API_EMAIL", "")


class CloudflareHandler(ZoneMixin, DnsMixin, SslMixin, WorkersMixin):
    """
    Cloudflare API 处理器，封装所有 SDK 调用。
    Cloudflare API handler that wraps all SDK calls.

    通过 Mixin 模式组合 Zone、DNS、SSL 和 Workers/AI/Analytics 功能。
    Composes Zone, DNS, SSL and Workers/AI/Analytics features via Mixin pattern.
    """

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
