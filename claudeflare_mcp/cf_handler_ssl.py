"""
SSL/TLS 与自定义主机名相关 Cloudflare API 方法 Mixin。
SSL/TLS and custom hostname related Cloudflare API methods mixin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import cloudflare


class SslMixin:
    """
    SSL/TLS 和自定义主机名操作 Mixin。
    SSL/TLS and custom hostname operations mixin.

    需要宿主类实现 _get_client()。
    Requires host class to implement _get_client().
    """

    def _get_client(self) -> cloudflare.AsyncCloudflare:
        raise NotImplementedError

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
            cert_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
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

    async def list_custom_hostnames(self, zone_id: str) -> list[dict[str, object]]:
        """
        列出 Zone 的自定义主机名。
        List custom hostnames for a zone.
        """
        async with self._get_client() as client:
            page = await client.custom_hostnames.list(zone_id=zone_id)
            hostname_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
            return [
                {
                    "id": h.id,  # type: ignore[attr-defined]
                    "hostname": h.hostname,  # type: ignore[attr-defined]
                    "status": h.status,  # type: ignore[attr-defined]
                }
                for h in hostname_items
            ]

    async def create_custom_hostname(
        self,
        zone_id: str,
        hostname: str,
        min_tls_version: str = "1.2",
    ) -> dict[str, object]:
        """
        创建自定义主机名（默认使用 HTTP DV 证书）。
        Create a custom hostname (defaults to HTTP DV certificate).
        """
        ssl_config: dict[str, object] = {
            "method": "http",
            "type": "dv",
            "settings": {"min_tls_version": min_tls_version},
        }
        async with self._get_client() as client:
            result = await client.custom_hostnames.create(
                zone_id=zone_id,
                hostname=hostname,
                ssl=ssl_config,  # type: ignore[arg-type]
            )
            return {
                "id": result.id,  # type: ignore[union-attr]
                "hostname": result.hostname,  # type: ignore[union-attr]
                "status": result.status,  # type: ignore[union-attr]
            }

    async def update_custom_hostname(
        self,
        zone_id: str,
        custom_hostname_id: str,
        min_tls_version: str = "1.2",
    ) -> dict[str, object]:
        """
        更新自定义主机名的 SSL 设置。
        Update SSL settings for a custom hostname.
        """
        ssl_config: dict[str, object] = {
            "method": "http",
            "type": "dv",
            "settings": {"min_tls_version": min_tls_version},
        }
        async with self._get_client() as client:
            result = await client.custom_hostnames.edit(
                custom_hostname_id,
                zone_id=zone_id,
                ssl=ssl_config,  # type: ignore[arg-type]
            )
            return {
                "id": result.id,  # type: ignore[union-attr]
                "hostname": result.hostname,  # type: ignore[union-attr]
                "status": result.status,  # type: ignore[union-attr]
            }

    async def delete_custom_hostname(
        self, zone_id: str, custom_hostname_id: str
    ) -> bool:
        """
        删除自定义主机名。
        Delete a custom hostname.
        """
        async with self._get_client() as client:
            await client.custom_hostnames.delete(
                custom_hostname_id, zone_id=zone_id
            )
            return True
