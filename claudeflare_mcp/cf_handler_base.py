"""
Cloudflare Handler 基础模块：共享常量、类型别名与抽象基类。
Cloudflare Handler base module: shared constants, type aliases and abstract base class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import cloudflare

# Cloudflare REST API 基础 URL
_CF_API_BASE = "https://api.cloudflare.com/client/v4"

# 共享类型别名
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


class CloudflareBase:
    """
    Cloudflare Handler 抽象基类，声明所有 Mixin 共享的接口方法。
    Abstract base class declaring shared interface methods for all Mixins.

    子类（CloudflareHandler）必须提供具体实现。
    Subclass (CloudflareHandler) must provide concrete implementations.
    """

    def _get_client(self) -> cloudflare.AsyncCloudflare:
        """
        创建 Cloudflare 异步客户端。
        Create async Cloudflare client.
        """
        raise NotImplementedError

    def _get_auth_headers(self) -> dict[str, str]:
        """
        获取 HTTP 请求认证头。
        Get HTTP authentication headers.
        """
        raise NotImplementedError
