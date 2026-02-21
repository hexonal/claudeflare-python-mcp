"""
DNS 相关 Cloudflare API 方法 Mixin。
DNS-related Cloudflare API methods mixin.
"""

from __future__ import annotations

import httpx

from .cf_handler_base import (
    CloudflareBase,
    CreateDnsRecordParams,
    DnsRecordData,
    UpdateDnsRecordParams,
    _CF_API_BASE,
)


class DnsMixin(CloudflareBase):
    """
    DNS 操作 Mixin，提供 DNS 记录和 DNSSEC 相关方法。
    DNS operations mixin providing DNS record and DNSSEC methods.
    """

    async def list_dns_records(self, zone_id: str) -> list[DnsRecordData]:
        """
        列出指定 Zone 的所有 DNS 记录。
        List all DNS records for a zone.
        """
        async with self._get_client() as client:
            page = await client.dns.records.list(zone_id=zone_id)
            record_items: list[object] = (
                page.result if hasattr(page, "result") else list(page)  # type: ignore[attr-defined]
            )
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
        params: CreateDnsRecordParams,
    ) -> DnsRecordData:
        """
        创建 DNS 记录。
        Create a DNS record.
        """
        async with self._get_client() as client:
            record = await client.dns.records.create(  # type: ignore[call-overload]
                zone_id=zone_id,
                type=params["record_type"],  # pyright: ignore[reportArgumentType]
                name=params["name"],
                content=params["content"],
                ttl=params["ttl"],
                proxied=params["proxied"],
            )
            return {
                "id": record.id,  # type: ignore[union-attr]
                "type": record.type,  # type: ignore[union-attr]
                "name": record.name,  # type: ignore[union-attr]
                "content": record.content,  # type: ignore[union-attr]
                "proxied": record.proxied,  # type: ignore[union-attr]
            }

    async def update_dns_record(
        self,
        zone_id: str,
        record_id: str,
        params: UpdateDnsRecordParams,
    ) -> DnsRecordData:
        """
        更新 DNS 记录内容（先获取现有记录保留 name/type，再 PATCH 更新）。
        Update DNS record content (fetches existing record to preserve name/type, then PATCH).
        """
        async with self._get_client() as client:
            existing = await client.dns.records.get(record_id, zone_id=zone_id)
            proxied = params["proxied"]
            # proxied 为 None 时保留现有值，否则使用传入值
            effective_proxied = (
                proxied if proxied is not None else existing.proxied  # type: ignore[union-attr]
            )
            record = await client.dns.records.edit(
                record_id,
                zone_id=zone_id,
                name=existing.name,  # type: ignore[union-attr]
                type=existing.type,  # type: ignore[union-attr, arg-type]
                content=params["content"],
                ttl=params["ttl"],
                proxied=effective_proxied,  # pyright: ignore[reportArgumentType]
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
