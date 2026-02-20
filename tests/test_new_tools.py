"""
新增 19 个工具的单元测试（Handler 层 + MCP 工具层）。
Unit tests for the 19 newly added tools (handler layer + MCP tool layer).
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCloudflareHandlerNew:
    """新增 Handler 方法的 SDK-mock 层测试。"""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """设置测试环境变量。"""
        monkeypatch.setenv("CF_API_TOKEN", "test-token-xxx")
        monkeypatch.setenv("CF_ACCOUNT_ID", "test-account-id")

    # ── Caching ────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_purge_cache_everything(self) -> None:
        """purge_cache purge_everything=True 时调用正确的 SDK 方法并返回成功。"""
        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.cache.purge = AsyncMock(return_value=None)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.purge_cache("zone-123", purge_everything=True)

        assert result["purged"] is True
        assert result["zone_id"] == "zone-123"

    @pytest.mark.asyncio
    async def test_get_cache_settings_success(self) -> None:
        """get_cache_settings 通过 httpx 返回缓存相关配置键。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "cache_level", "value": "aggressive"},
                {"id": "browser_cache_ttl", "value": 14400},
                {"id": "ssl", "value": "full"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.get = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_cache_settings("zone-123")

        assert result["cache_level"] == "aggressive"
        assert result["browser_cache_ttl"] == 14400
        # ssl 不在 _CACHE_KEYS 中，应被过滤
        assert "ssl" not in result

    @pytest.mark.asyncio
    async def test_get_speed_settings_success(self) -> None:
        """get_speed_settings 过滤返回速度优化相关设置。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "brotli", "value": "on"},
                {"id": "http2", "value": "on"},
                {"id": "cache_level", "value": "aggressive"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.get = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_speed_settings("zone-123")

        assert result["brotli"] == "on"
        assert result["http2"] == "on"
        assert "cache_level" not in result

    # ── Security ───────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_firewall_rules_success(self) -> None:
        """list_firewall_rules 成功返回防火墙规则列表。"""
        mock_rule = MagicMock()
        mock_rule.id = "rule-001"
        mock_rule.mode = "block"
        mock_rule.notes = "Block bad IP"
        mock_rule.configuration = {"target": "ip", "value": "1.2.3.4"}

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.firewall.access_rules.list = AsyncMock(return_value=[mock_rule])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_firewall_rules("zone-123")

        assert len(result) == 1
        assert result[0]["id"] == "rule-001"
        assert result[0]["mode"] == "block"

    @pytest.mark.asyncio
    async def test_get_security_settings_success(self) -> None:
        """get_security_settings 过滤返回安全相关设置。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "security_level", "value": "high"},
                {"id": "waf", "value": "on"},
                {"id": "http2", "value": "on"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.get = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_security_settings("zone-123")

        assert result["security_level"] == "high"
        assert result["waf"] == "on"
        assert "http2" not in result

    # ── SSL/TLS ────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_ssl_settings_success(self) -> None:
        """get_ssl_settings 成功返回 SSL 通用设置。"""
        mock_ssl = MagicMock()
        mock_ssl.enabled = True
        mock_ssl.certificate_authority = "digicert"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.ssl.universal.settings.get = AsyncMock(return_value=mock_ssl)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_ssl_settings("zone-123")

        assert result["enabled"] is True
        assert result["certificate_authority"] == "digicert"

    @pytest.mark.asyncio
    async def test_list_ssl_certificates_success(self) -> None:
        """list_ssl_certificates 成功返回证书包列表。"""
        mock_cert = MagicMock()
        mock_cert.id = "cert-abc"
        mock_cert.type = "advanced"
        mock_cert.status = "active"
        mock_cert.hosts = ["*.example.com"]

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.ssl.certificate_packs.list = AsyncMock(return_value=[mock_cert])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_ssl_certificates("zone-123")

        assert len(result) == 1
        assert result[0]["id"] == "cert-abc"
        assert result[0]["status"] == "active"

    # ── Custom Hostnames ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_custom_hostnames_success(self) -> None:
        """list_custom_hostnames 成功返回自定义主机名列表。"""
        mock_hostname = MagicMock()
        mock_hostname.id = "chn-001"
        mock_hostname.hostname = "app.partner.com"
        mock_hostname.status = "active"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.custom_hostnames.list = AsyncMock(return_value=[mock_hostname])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_custom_hostnames("zone-123")

        assert result[0]["hostname"] == "app.partner.com"

    @pytest.mark.asyncio
    async def test_create_custom_hostname_success(self) -> None:
        """create_custom_hostname 成功创建并返回新主机名数据。"""
        mock_result = MagicMock()
        mock_result.id = "chn-new"
        mock_result.hostname = "new.partner.com"
        mock_result.status = "pending"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.custom_hostnames.create = AsyncMock(return_value=mock_result)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.create_custom_hostname("zone-123", "new.partner.com")

        assert result["hostname"] == "new.partner.com"
        assert result["status"] == "pending"

    # ── Email Routing ──────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_email_routing_success(self) -> None:
        """get_email_routing 成功返回邮件路由设置。"""
        mock_routing = MagicMock()
        mock_routing.id = "routing-001"
        mock_routing.name = "example.com"
        mock_routing.enabled = True
        mock_routing.status = "ready"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.email_routing.get = AsyncMock(return_value=mock_routing)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_email_routing("zone-123")

        assert result["enabled"] is True
        assert result["status"] == "ready"

    @pytest.mark.asyncio
    async def test_list_email_routing_rules_success(self) -> None:
        """list_email_routing_rules 成功返回路由规则列表。"""
        mock_rule = MagicMock()
        mock_rule.id = "rule-email-001"
        mock_rule.name = "Forward to admin"
        mock_rule.enabled = True
        mock_rule.priority = 0

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.email_routing.rules.list = AsyncMock(return_value=[mock_rule])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_email_routing_rules("zone-123")

        assert result[0]["name"] == "Forward to admin"

    # ── DNS 扩展 ───────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_dnssec_success(self) -> None:
        """get_dnssec 成功返回 DNSSEC 状态。"""
        mock_dnssec = MagicMock()
        mock_dnssec.status = "active"
        mock_dnssec.ds = "DS record content"
        mock_dnssec.algorithm = "13"
        mock_dnssec.digest_type = "2"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.dns.dnssec.get = AsyncMock(return_value=mock_dnssec)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_dnssec("zone-123")

        assert result["status"] == "active"
        assert result["algorithm"] == "13"

    @pytest.mark.asyncio
    async def test_get_dns_settings_success(self) -> None:
        """get_dns_settings 成功通过 httpx 返回 DNS 基础配置。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "zone_mode": "full",
                "flatten_all_cnames": False,
                "foundation_dns": False,
            }
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.get = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_dns_settings("zone-123")

        assert result["zone_mode"] == "full"
        assert result["flatten_all_cnames"] is False

    # ── Analytics ──────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_zone_analytics_success(self) -> None:
        """get_zone_analytics 通过 GraphQL Analytics API 返回聚合流量统计数据。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "viewer": {
                    "zones": [
                        {
                            "httpRequests1hGroups": [
                                {
                                    "sum": {
                                        "requests": 600,
                                        "cachedRequests": 500,
                                        "bytes": 6000000,
                                        "cachedBytes": 5000000,
                                        "threats": 3,
                                        "pageViews": 550,
                                    }
                                },
                                {
                                    "sum": {
                                        "requests": 400,
                                        "cachedRequests": 300,
                                        "bytes": 4000000,
                                        "cachedBytes": 3000000,
                                        "threats": 2,
                                        "pageViews": 350,
                                    }
                                },
                            ]
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.post = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_zone_analytics("zone-123")

        assert result["requests"]["total"] == 1000  # type: ignore[index]
        assert result["requests"]["cached"] == 800  # type: ignore[index]
        assert result["requests"]["uncached"] == 200  # type: ignore[index]
        assert result["threats"]["total"] == 5  # type: ignore[index]
        assert result["pageviews"]["total"] == 900  # type: ignore[index]

    # ── AI ─────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_ai_models_success(self) -> None:
        """list_ai_models 成功通过 httpx 返回模型列表。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "@cf/meta/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "task": {}},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.get = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_ai_models("account-123")

        assert len(result) == 1
        assert result[0]["name"] == "Llama 3.1 8B"

    @pytest.mark.asyncio
    async def test_run_ai_success(self) -> None:
        """run_ai 成功通过 httpx POST 调用模型并返回结果。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"response": "Hello from AI!"}
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.post = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.run_ai("account-123", "@cf/meta/llama-3.1-8b-instruct", "Hello")

        assert result["response"] == "Hello from AI!"

    # ── Workers ────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_workers_success(self) -> None:
        """list_workers 成功返回 Worker 脚本列表。"""
        mock_script = MagicMock()
        mock_script.id = "my-worker"
        mock_script.created_on = "2024-01-01T00:00:00Z"
        mock_script.modified_on = "2024-06-01T00:00:00Z"
        mock_script.etag = "etag-abc"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.workers.scripts.list = AsyncMock(return_value=[mock_script])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_workers("account-123")

        assert result[0]["id"] == "my-worker"

    @pytest.mark.asyncio
    async def test_list_worker_routes_success(self) -> None:
        """list_worker_routes 成功返回 Worker 路由规则列表。"""
        mock_route = MagicMock()
        mock_route.id = "route-001"
        mock_route.pattern = "example.com/*"
        mock_route.script = "my-worker"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.workers.routes.list = AsyncMock(return_value=[mock_route])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_worker_routes("zone-123")

        assert result[0]["pattern"] == "example.com/*"
        assert result[0]["script"] == "my-worker"

    @pytest.mark.asyncio
    async def test_get_worker_success(self) -> None:
        """get_worker 成功通过 httpx 列表接口过滤返回脚本元数据。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "id": "my-worker",
                    "created_on": "2024-01-01T00:00:00Z",
                    "modified_on": "2024-06-01T00:00:00Z",
                    "etag": "etag-xyz",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("httpx.AsyncClient") as mock_http_cls,
        ):
            mock_http_client = AsyncMock()
            mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_http_client.get = AsyncMock(return_value=mock_response)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.get_worker("account-123", "my-worker")

        assert result["id"] == "my-worker"
        assert result["etag"] == "etag-xyz"


class TestMcpToolsNew:
    """新增 MCP 工具函数的集成测试（mock handler 层）。"""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CF_API_TOKEN", "test-token")

    # ── Caching ────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_purge_cache_success(self) -> None:
        """purge_cache 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import purge_cache

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.purge_cache.return_value = {"purged": True, "zone_id": "zone-123"}

            result = await purge_cache("zone-123", purge_everything=True)
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["purged"] is True

    @pytest.mark.asyncio
    async def test_purge_cache_permission_denied(self) -> None:
        """purge_cache 权限不足时返回包含"权限"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import purge_cache

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.purge_cache.side_effect = cloudflare.PermissionDeniedError(
                message="Permission denied",
                response=MagicMock(),
                body={},
            )

            result = await purge_cache("zone-123", purge_everything=True)
            data = json.loads(result)

        assert data["status"] == "error"
        assert "权限" in data["message"]

    @pytest.mark.asyncio
    async def test_get_cache_settings_success(self) -> None:
        """get_cache_settings 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_cache_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_cache_settings.return_value = {
                "cache_level": "aggressive",
                "browser_cache_ttl": 14400,
            }

            result = await get_cache_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["cache_level"] == "aggressive"

    # ── Speed ──────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_speed_settings_success(self) -> None:
        """get_speed_settings 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_speed_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_speed_settings.return_value = {"brotli": "on", "http2": "on"}

            result = await get_speed_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["brotli"] == "on"

    @pytest.mark.asyncio
    async def test_get_speed_settings_not_found(self) -> None:
        """get_speed_settings Zone 不存在时返回含 zone_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import get_speed_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_speed_settings.side_effect = cloudflare.NotFoundError(
                message="Not found",
                response=MagicMock(),
                body={},
            )

            result = await get_speed_settings("zone-bad")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "zone-bad" in data["message"]

    # ── Security ───────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_firewall_rules_success(self) -> None:
        """list_firewall_rules 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_firewall_rules

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_firewall_rules.return_value = [
                {"id": "r1", "mode": "block", "notes": "Test", "configuration": {}}
            ]

            result = await list_firewall_rules("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["mode"] == "block"

    @pytest.mark.asyncio
    async def test_list_firewall_rules_auth_error(self) -> None:
        """list_firewall_rules Token 无效时返回包含"无效"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_firewall_rules

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_firewall_rules.side_effect = cloudflare.AuthenticationError(
                message="Invalid",
                response=MagicMock(),
                body={},
            )

            result = await list_firewall_rules("zone-123")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_get_security_settings_success(self) -> None:
        """get_security_settings 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_security_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_security_settings.return_value = {
                "security_level": "high",
                "waf": "on",
            }

            result = await get_security_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["security_level"] == "high"

    # ── SSL/TLS ────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_ssl_settings_success(self) -> None:
        """get_ssl_settings 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_ssl_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_ssl_settings.return_value = {
                "enabled": True,
                "certificate_authority": "digicert",
            }

            result = await get_ssl_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_list_ssl_certificates_success(self) -> None:
        """list_ssl_certificates 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_ssl_certificates

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_ssl_certificates.return_value = [
                {"id": "cert-1", "type": "advanced", "status": "active", "hosts": ["*.example.com"]}
            ]

            result = await list_ssl_certificates("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["status"] == "active"

    # ── Custom Hostnames ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_custom_hostnames_success(self) -> None:
        """list_custom_hostnames 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_custom_hostnames

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_custom_hostnames.return_value = [
                {"id": "chn-1", "hostname": "app.partner.com", "status": "active"}
            ]

            result = await list_custom_hostnames("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["hostname"] == "app.partner.com"

    @pytest.mark.asyncio
    async def test_create_custom_hostname_success(self) -> None:
        """create_custom_hostname 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import create_custom_hostname

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.create_custom_hostname.return_value = {
                "id": "chn-new",
                "hostname": "new.partner.com",
                "status": "pending",
            }

            result = await create_custom_hostname("zone-123", "new.partner.com")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["hostname"] == "new.partner.com"

    @pytest.mark.asyncio
    async def test_create_custom_hostname_not_found(self) -> None:
        """create_custom_hostname Zone 不存在时返回含 zone_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import create_custom_hostname

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.create_custom_hostname.side_effect = cloudflare.NotFoundError(
                message="Not found",
                response=MagicMock(),
                body={},
            )

            result = await create_custom_hostname("zone-bad", "test.partner.com")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "zone-bad" in data["message"]

    # ── Email Routing ──────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_email_routing_success(self) -> None:
        """get_email_routing 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_email_routing

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_email_routing.return_value = {
                "id": "r1",
                "name": "example.com",
                "enabled": True,
                "status": "ready",
            }

            result = await get_email_routing("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_list_email_routing_rules_success(self) -> None:
        """list_email_routing_rules 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_email_routing_rules

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_email_routing_rules.return_value = [
                {"id": "er1", "name": "Forward", "enabled": True, "priority": 0}
            ]

            result = await list_email_routing_rules("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["name"] == "Forward"

    # ── DNS 扩展 ───────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_dnssec_success(self) -> None:
        """get_dnssec 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_dnssec

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_dnssec.return_value = {
                "status": "active",
                "ds": "DS...",
                "algorithm": "13",
                "digest_type": "2",
            }

            result = await get_dnssec("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_dnssec_not_found(self) -> None:
        """get_dnssec Zone 不存在时返回含 zone_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import get_dnssec

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_dnssec.side_effect = cloudflare.NotFoundError(
                message="Not found",
                response=MagicMock(),
                body={},
            )

            result = await get_dnssec("zone-bad")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "zone-bad" in data["message"]

    @pytest.mark.asyncio
    async def test_get_dns_settings_success(self) -> None:
        """get_dns_settings 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_dns_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_dns_settings.return_value = {
                "zone_mode": "full",
                "flatten_all_cnames": False,
                "foundation_dns": False,
            }

            result = await get_dns_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["zone_mode"] == "full"

    # ── Analytics ──────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_zone_analytics_success(self) -> None:
        """get_zone_analytics 工具函数返回合法 JSON 成功响应（GraphQL 聚合格式）。"""
        from claudeflare_mcp import get_zone_analytics

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_zone_analytics.return_value = {
                "requests": {"total": 1000, "cached": 800, "uncached": 200},
                "bandwidth": {"total": 10000000, "cached": 8000000, "uncached": 2000000},
                "threats": {"total": 5},
                "pageviews": {"total": 900},
            }

            result = await get_zone_analytics("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["requests"]["total"] == 1000
        assert data["data"]["requests"]["uncached"] == 200

    @pytest.mark.asyncio
    async def test_get_zone_analytics_generic_error(self) -> None:
        """get_zone_analytics 未知异常时返回包含异常消息的错误响应。"""
        from claudeflare_mcp import get_zone_analytics

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_zone_analytics.side_effect = Exception("analytics error")

            result = await get_zone_analytics("zone-123")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "analytics error" in data["message"]

    # ── AI ─────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_ai_models_success(self) -> None:
        """list_ai_models 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_ai_models

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_ai_models.return_value = [
                {"id": "@cf/meta/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "task": {}}
            ]

            result = await list_ai_models("account-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["name"] == "Llama 3.1 8B"

    @pytest.mark.asyncio
    async def test_list_ai_models_auth_error(self) -> None:
        """list_ai_models Token 无效时返回包含"无效"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_ai_models

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_ai_models.side_effect = cloudflare.AuthenticationError(
                message="Invalid token",
                response=MagicMock(),
                body={},
            )

            result = await list_ai_models("account-123")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_run_ai_success(self) -> None:
        """run_ai 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import run_ai

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.run_ai.return_value = {"response": "Hello from AI!"}

            result = await run_ai("account-123", "@cf/meta/llama-3.1-8b-instruct", "Hello")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["response"] == "Hello from AI!"

    @pytest.mark.asyncio
    async def test_run_ai_connection_error(self) -> None:
        """run_ai 连接失败时返回包含"连接"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import run_ai

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.run_ai.side_effect = cloudflare.APIConnectionError(
                request=MagicMock(),
            )

            result = await run_ai("account-123", "@cf/meta/llama", "Hello")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "连接" in data["message"]

    # ── Workers ────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_workers_success(self) -> None:
        """list_workers 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_workers

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_workers.return_value = [
                {"id": "my-worker", "created_on": "2024-01-01", "modified_on": "2024-06-01", "etag": "e1"}
            ]

            result = await list_workers("account-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["id"] == "my-worker"

    @pytest.mark.asyncio
    async def test_list_workers_auth_error(self) -> None:
        """list_workers Token 无效时返回包含"无效"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_workers

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_workers.side_effect = cloudflare.AuthenticationError(
                message="Invalid token",
                response=MagicMock(),
                body={},
            )

            result = await list_workers("account-123")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_list_worker_routes_success(self) -> None:
        """list_worker_routes 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_worker_routes

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_worker_routes.return_value = [
                {"id": "rt1", "pattern": "example.com/*", "script": "my-worker"}
            ]

            result = await list_worker_routes("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["pattern"] == "example.com/*"

    @pytest.mark.asyncio
    async def test_get_worker_success(self) -> None:
        """get_worker 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_worker

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_worker.return_value = {
                "id": "my-worker",
                "created_on": "2024-01-01",
                "modified_on": "2024-06-01",
                "etag": "etag-xyz",
            }

            result = await get_worker("account-123", "my-worker")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["etag"] == "etag-xyz"

    @pytest.mark.asyncio
    async def test_get_worker_not_found(self) -> None:
        """get_worker 脚本不存在时返回含脚本名的错误响应。"""
        import cloudflare

        from claudeflare_mcp import get_worker

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_worker.side_effect = cloudflare.NotFoundError(
                message="Not found",
                response=MagicMock(),
                body={},
            )

            result = await get_worker("account-123", "bad-worker")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "bad-worker" in data["message"]
