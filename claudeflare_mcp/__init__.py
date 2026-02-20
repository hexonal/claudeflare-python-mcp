"""
Cloudflare MCP 服务器，提供域名配置与常用 API 工具集合。
Cloudflare MCP server providing domain config and common API tools.
"""

import json

import cloudflare
from fastmcp import FastMCP

from .cf_handler import CloudflareHandler

mcp = FastMCP("Cloudflare MCP Server")

__all__ = [
    "mcp",
    "CloudflareHandler",
    # DNS
    "list_zones",
    "list_dns_records",
    "create_dns_record",
    "update_dns_record",
    "delete_dns_record",
    "get_zone_settings",
    # Caching
    "purge_cache",
    "get_cache_settings",
    # Speed
    "get_speed_settings",
    # Security
    "list_firewall_rules",
    "get_security_settings",
    # SSL/TLS
    "get_ssl_settings",
    "list_ssl_certificates",
    # Custom Hostnames
    "list_custom_hostnames",
    "create_custom_hostname",
    # Email Routing
    "get_email_routing",
    "list_email_routing_rules",
    # DNS 扩展
    "get_dnssec",
    "get_dns_settings",
    # Analytics
    "get_zone_analytics",
    # AI
    "list_ai_models",
    "run_ai",
    # Workers
    "list_workers",
    "list_worker_routes",
    "get_worker",
]


def _success(data: object) -> str:
    """构建成功响应 JSON。Build success response JSON."""
    return json.dumps({"status": "success", "data": data, "message": ""}, ensure_ascii=False)


def _error(message: str) -> str:
    """构建错误响应 JSON。Build error response JSON."""
    return json.dumps({"status": "error", "data": None, "message": message}, ensure_ascii=False)


@mcp.tool()
async def list_zones() -> str:
    """
    列出 Cloudflare 账户下的所有 Zone（域名）。
    List all Zones (domains) in the Cloudflare account.
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_zones()
        return _success(data)
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效，请检查 Token 是否正确")
    except cloudflare.APIConnectionError as exc:
        return _error(f"连接 Cloudflare API 失败: {exc}")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def list_dns_records(zone_id: str) -> str:
    """
    列出指定 Zone 的所有 DNS 记录。
    List all DNS records for a specific Zone.

    Args:
        zone_id: Zone ID，可通过 list_zones 获取
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_dns_records(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def create_dns_record(
    zone_id: str,
    record_type: str,
    name: str,
    content: str,
    ttl: int = 1,
    proxied: bool = False,
) -> str:
    """
    创建 DNS 记录。
    Create a DNS record.

    Args:
        zone_id: Zone ID
        record_type: 记录类型（A/AAAA/CNAME/MX/TXT 等）
        name: 记录名称（如 www.example.com）
        content: 记录内容（如 IP 地址）
        ttl: TTL 秒数，1 表示自动
        proxied: 是否开启 Cloudflare 代理（小黄云），默认 False
    """
    handler = CloudflareHandler()
    try:
        data = await handler.create_dns_record(zone_id, record_type, name, content, ttl, proxied)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def update_dns_record(
    zone_id: str,
    record_id: str,
    content: str,
    ttl: int = 1,
    proxied: bool | None = None,
) -> str:
    """
    更新 DNS 记录内容。
    Update DNS record content.

    Args:
        zone_id: Zone ID
        record_id: DNS 记录 ID，可通过 list_dns_records 获取
        content: 新的记录内容（如新 IP 地址）
        ttl: TTL 秒数，1 表示自动
        proxied: 是否开启 Cloudflare 代理（小黄云），None 表示保持现有值
    """
    handler = CloudflareHandler()
    try:
        data = await handler.update_dns_record(zone_id, record_id, content, ttl, proxied)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"DNS 记录 {record_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def delete_dns_record(zone_id: str, record_id: str) -> str:
    """
    删除 DNS 记录。
    Delete a DNS record.

    Args:
        zone_id: Zone ID
        record_id: DNS 记录 ID，可通过 list_dns_records 获取
    """
    handler = CloudflareHandler()
    try:
        await handler.delete_dns_record(zone_id, record_id)
        return _success({"deleted": True, "record_id": record_id})
    except cloudflare.NotFoundError:
        return _error(f"DNS 记录 {record_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def get_zone_settings(zone_id: str) -> str:
    """
    获取 Zone 的安全和性能配置。
    Get security and performance settings for a Zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_zone_settings(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


# ── Caching ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def purge_cache(
    zone_id: str,
    files: str = "",
    tags: str = "",
    purge_everything: bool = False,
) -> str:
    """
    清除 Zone 缓存（全部、按 URL 或按 Cache-Tag）。
    Purge zone cache (everything, by URLs, or by cache tags).

    Args:
        zone_id: Zone ID
        files: 逗号分隔的 URL 列表（与 tags/purge_everything 互斥）
        tags: 逗号分隔的 Cache-Tag 列表（与 files/purge_everything 互斥）
        purge_everything: 清除所有缓存（优先级最高）
    """
    handler = CloudflareHandler()
    try:
        data = await handler.purge_cache(zone_id, files, tags, purge_everything)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.PermissionDeniedError:
        return _error("无权限清除缓存，请检查 API Token 的 Cache Purge 权限")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def get_cache_settings(zone_id: str) -> str:
    """
    获取 Zone 的缓存配置（缓存级别、浏览器缓存 TTL 等）。
    Get cache settings for a zone (cache level, browser TTL, etc.).

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_cache_settings(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


# ── Speed ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_speed_settings(zone_id: str) -> str:
    """
    获取 Zone 的性能优化配置（Brotli、HTTP/2、Rocket Loader 等）。
    Get speed optimization settings for a zone (Brotli, HTTP/2, Rocket Loader, etc.).

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_speed_settings(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


# ── Security ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_firewall_rules(zone_id: str) -> str:
    """
    列出 Zone 的防火墙访问规则。
    List firewall access rules for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_firewall_rules(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def get_security_settings(zone_id: str) -> str:
    """
    获取 Zone 的安全配置（安全级别、WAF、挑战 TTL 等）。
    Get security settings for a zone (security level, WAF, challenge TTL, etc.).

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_security_settings(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


# ── SSL/TLS ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_ssl_settings(zone_id: str) -> str:
    """
    获取 Zone 的 SSL/TLS 通用设置。
    Get SSL/TLS universal settings for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_ssl_settings(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def list_ssl_certificates(zone_id: str) -> str:
    """
    列出 Zone 的 SSL 证书包。
    List SSL certificate packs for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_ssl_certificates(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


# ── Custom Hostnames ──────────────────────────────────────────────────────────


@mcp.tool()
async def list_custom_hostnames(zone_id: str) -> str:
    """
    列出 Zone 的自定义主机名。
    List custom hostnames for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_custom_hostnames(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def create_custom_hostname(
    zone_id: str,
    hostname: str,
    min_tls_version: str = "1.2",
) -> str:
    """
    创建自定义主机名（使用 HTTP DV 证书）。
    Create a custom hostname (using HTTP DV certificate).

    Args:
        zone_id: Zone ID
        hostname: 要添加的自定义主机名（如 app.partner.com）
        min_tls_version: 最低 TLS 版本（1.0/1.1/1.2/1.3），默认 1.2
    """
    handler = CloudflareHandler()
    try:
        data = await handler.create_custom_hostname(zone_id, hostname, min_tls_version)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def update_custom_hostname(
    zone_id: str,
    custom_hostname_id: str,
    min_tls_version: str = "1.2",
) -> str:
    """
    更新自定义主机名的 SSL 设置。
    Update SSL settings for a custom hostname.

    Args:
        zone_id: Zone ID
        custom_hostname_id: 自定义主机名 ID，可通过 list_custom_hostnames 获取
        min_tls_version: 最低 TLS 版本（1.0/1.1/1.2/1.3），默认 1.2
    """
    handler = CloudflareHandler()
    try:
        data = await handler.update_custom_hostname(zone_id, custom_hostname_id, min_tls_version)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Custom hostname {custom_hostname_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def delete_custom_hostname(zone_id: str, custom_hostname_id: str) -> str:
    """
    删除自定义主机名。
    Delete a custom hostname.

    Args:
        zone_id: Zone ID
        custom_hostname_id: 自定义主机名 ID，可通过 list_custom_hostnames 获取
    """
    handler = CloudflareHandler()
    try:
        result = await handler.delete_custom_hostname(zone_id, custom_hostname_id)
        return _success({"deleted": result, "custom_hostname_id": custom_hostname_id})
    except cloudflare.NotFoundError:
        return _error(f"Custom hostname {custom_hostname_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


# ── Email Routing ─────────────────────────────────────────────────────────────


@mcp.tool()
async def get_email_routing(zone_id: str) -> str:
    """
    获取 Zone 的邮件路由设置。
    Get email routing settings for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_email_routing(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def list_email_routing_rules(zone_id: str) -> str:
    """
    列出 Zone 的邮件路由规则。
    List email routing rules for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_email_routing_rules(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


# ── DNS 扩展 ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_dnssec(zone_id: str) -> str:
    """
    获取 Zone 的 DNSSEC 状态与配置。
    Get DNSSEC status and configuration for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_dnssec(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def get_dns_settings(zone_id: str) -> str:
    """
    获取 Zone 的 DNS 基础设置（Zone 模式、CNAME 展开等）。
    Get DNS infrastructure settings for a zone (zone mode, CNAME flattening, etc.).

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_dns_settings(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


# ── Analytics ─────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_zone_analytics(zone_id: str) -> str:
    """
    获取 Zone 最近 24 小时的流量分析（请求数、带宽、威胁、页面浏览）。
    Get zone traffic analytics for the last 24 hours (requests, bandwidth, threats, pageviews).

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_zone_analytics(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


# ── AI (Workers AI) ───────────────────────────────────────────────────────────


@mcp.tool()
async def list_ai_models(account_id: str) -> str:
    """
    列出账户下可用的 Workers AI 模型。
    List available Workers AI models for an account.

    Args:
        account_id: Cloudflare 账户 ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_ai_models(account_id)
        return _success(data)
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except cloudflare.APIConnectionError as exc:
        return _error(f"连接 Cloudflare API 失败: {exc}")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def run_ai(account_id: str, model_name: str, prompt: str) -> str:
    """
    调用 Workers AI 模型执行推理。
    Run inference on a Workers AI model.

    Args:
        account_id: Cloudflare 账户 ID
        model_name: 模型名称（如 @cf/meta/llama-3.1-8b-instruct）
        prompt: 用户输入的提示词
    """
    handler = CloudflareHandler()
    try:
        data = await handler.run_ai(account_id, model_name, prompt)
        return _success(data)
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except cloudflare.APIConnectionError as exc:
        return _error(f"连接 Cloudflare API 失败: {exc}")
    except Exception as exc:
        return _error(str(exc))


# ── Workers ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_workers(account_id: str) -> str:
    """
    列出账户下的所有 Workers 脚本。
    List all Workers scripts for an account.

    Args:
        account_id: Cloudflare 账户 ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_workers(account_id)
        return _success(data)
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except cloudflare.APIConnectionError as exc:
        return _error(f"连接 Cloudflare API 失败: {exc}")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def list_worker_routes(zone_id: str) -> str:
    """
    列出 Zone 的 Worker 路由规则。
    List Worker routes for a zone.

    Args:
        zone_id: Zone ID
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_worker_routes(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def get_worker(account_id: str, script_name: str) -> str:
    """
    获取指定 Worker 脚本的元数据。
    Get metadata for a specific Worker script.

    Args:
        account_id: Cloudflare 账户 ID
        script_name: Worker 脚本名称
    """
    handler = CloudflareHandler()
    try:
        data = await handler.get_worker(account_id, script_name)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Worker 脚本 {script_name} 不存在")
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))
