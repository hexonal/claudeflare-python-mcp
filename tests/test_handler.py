"""
CloudflareHandler 单元测试。
Unit tests for CloudflareHandler.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCloudflareHandler:
    """CloudflareHandler 核心方法测试。"""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """设置测试环境变量。"""
        monkeypatch.setenv("CF_API_TOKEN", "test-token-xxx")
        monkeypatch.setenv("CF_ACCOUNT_ID", "test-account-id")

    @pytest.mark.asyncio
    async def test_list_zones_success(self) -> None:
        """list_zones 成功返回 Zone 列表。"""
        mock_zone = MagicMock()
        mock_zone.id = "zone-123"
        mock_zone.name = "example.com"
        mock_zone.status = "active"
        mock_zone.plan = None

        with patch("cloudflare.AsyncCloudflare") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.zones.list = AsyncMock(return_value=[mock_zone])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_zones()

        assert len(result) == 1
        assert result[0]["name"] == "example.com"
        assert result[0]["id"] == "zone-123"

    @pytest.mark.asyncio
    async def test_require_token_raises_on_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CF_API_TOKEN 和 CF_API_KEY 均未设置时应抛出 ValueError。"""
        monkeypatch.setenv("CF_API_TOKEN", "")
        monkeypatch.setenv("CF_API_KEY", "")
        monkeypatch.setenv("CF_API_EMAIL", "")

        import importlib

        import claudeflare_mcp.cf_handler as handler_mod

        importlib.reload(handler_mod)

        handler = handler_mod.CloudflareHandler()
        with pytest.raises(ValueError, match="CF_API_TOKEN"):
            handler._get_client()

    @pytest.mark.asyncio
    async def test_list_dns_records_success(self) -> None:
        """list_dns_records 成功返回 DNS 记录列表。"""
        mock_record = MagicMock()
        mock_record.id = "rec-456"
        mock_record.type = "A"
        mock_record.name = "www.example.com"
        mock_record.content = "1.2.3.4"
        mock_record.ttl = 3600
        mock_record.proxied = True

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.dns.records.list = AsyncMock(return_value=[mock_record])

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.list_dns_records("zone-123")

        assert len(result) == 1
        assert result[0]["id"] == "rec-456"
        assert result[0]["type"] == "A"
        assert result[0]["content"] == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_create_dns_record_success(self) -> None:
        """create_dns_record 成功创建并返回记录数据。"""
        mock_record = MagicMock()
        mock_record.id = "rec-new"
        mock_record.type = "A"
        mock_record.name = "api.example.com"
        mock_record.content = "5.6.7.8"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.dns.records.create = AsyncMock(return_value=mock_record)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.create_dns_record("zone-123", "A", "api.example.com", "5.6.7.8")

        assert result["id"] == "rec-new"
        assert result["content"] == "5.6.7.8"

    @pytest.mark.asyncio
    async def test_update_dns_record_success(self) -> None:
        """update_dns_record 先 get 再 edit，成功返回更新后的记录。"""
        mock_existing = MagicMock()
        mock_existing.name = "www.example.com"
        mock_existing.type = "A"

        mock_record = MagicMock()
        mock_record.id = "rec-456"
        mock_record.type = "A"
        mock_record.name = "www.example.com"
        mock_record.content = "9.9.9.9"

        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.dns.records.get = AsyncMock(return_value=mock_existing)
            mock_client.dns.records.edit = AsyncMock(return_value=mock_record)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.update_dns_record("zone-123", "rec-456", "9.9.9.9")

        assert result["id"] == "rec-456"
        assert result["content"] == "9.9.9.9"

    @pytest.mark.asyncio
    async def test_delete_dns_record_success(self) -> None:
        """delete_dns_record 成功删除并返回 True。"""
        with (
            patch("claudeflare_mcp.cf_handler._CF_API_TOKEN", "test-token"),
            patch("cloudflare.AsyncCloudflare") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.dns.records.delete = AsyncMock(return_value=None)

            from claudeflare_mcp.cf_handler import CloudflareHandler

            handler = CloudflareHandler()
            result = await handler.delete_dns_record("zone-123", "rec-456")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_zone_settings_success(self) -> None:
        """get_zone_settings 成功通过 httpx 返回设置字典。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "ssl", "value": "full"},
                {"id": "security_level", "value": "high"},
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
            result = await handler.get_zone_settings("zone-123")

        assert result["ssl"] == "full"
        assert result["security_level"] == "high"


class TestMcpTools:
    """MCP 工具函数集成测试。"""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CF_API_TOKEN", "test-token")

    @pytest.mark.asyncio
    async def test_list_zones_returns_success_json(self) -> None:
        """list_zones 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_zones

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_zones.return_value = [
                {"id": "z1", "name": "example.com", "status": "active", "plan": None}
            ]

            result = await list_zones()
            data = json.loads(result)

        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        assert data["data"][0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_list_zones_returns_error_on_exception(self) -> None:
        """list_zones 工具函数异常时返回合法 JSON 错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_zones

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_zones.side_effect = cloudflare.AuthenticationError(
                message="Invalid token",
                response=MagicMock(),
                body={},
            )

            result = await list_zones()
            data = json.loads(result)

        assert data["status"] == "error"
        assert data["data"] is None
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_list_dns_records_returns_success_json(self) -> None:
        """list_dns_records 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import list_dns_records

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_dns_records.return_value = [
                {"id": "r1", "type": "A", "name": "www.example.com", "content": "1.2.3.4"}
            ]

            result = await list_dns_records("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"][0]["type"] == "A"

    @pytest.mark.asyncio
    async def test_list_dns_records_not_found(self) -> None:
        """list_dns_records Zone 不存在时返回错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_dns_records

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_dns_records.side_effect = cloudflare.NotFoundError(
                message="Zone not found",
                response=MagicMock(),
                body={},
            )

            result = await list_dns_records("bad-zone")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "bad-zone" in data["message"]

    @pytest.mark.asyncio
    async def test_create_dns_record_returns_success_json(self) -> None:
        """create_dns_record 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import create_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.create_dns_record.return_value = {
                "id": "rec-new",
                "type": "A",
                "name": "api.example.com",
                "content": "5.6.7.8",
            }

            result = await create_dns_record("zone-123", "A", "api.example.com", "5.6.7.8")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["id"] == "rec-new"

    @pytest.mark.asyncio
    async def test_update_dns_record_returns_success_json(self) -> None:
        """update_dns_record 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import update_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.update_dns_record.return_value = {
                "id": "rec-456",
                "type": "A",
                "name": "www.example.com",
                "content": "9.9.9.9",
            }

            result = await update_dns_record("zone-123", "rec-456", "9.9.9.9")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["content"] == "9.9.9.9"

    @pytest.mark.asyncio
    async def test_delete_dns_record_returns_success_json(self) -> None:
        """delete_dns_record 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import delete_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.delete_dns_record.return_value = True

            result = await delete_dns_record("zone-123", "rec-456")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["deleted"] is True

    @pytest.mark.asyncio
    async def test_get_zone_settings_returns_success_json(self) -> None:
        """get_zone_settings 工具函数返回合法 JSON 成功响应。"""
        from claudeflare_mcp import get_zone_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_zone_settings.return_value = {"ssl": "full", "minify": "off"}

            result = await get_zone_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["ssl"] == "full"

    @pytest.mark.asyncio
    async def test_list_zones_api_connection_error(self) -> None:
        """list_zones 连接失败时返回包含"连接"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_zones

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_zones.side_effect = cloudflare.APIConnectionError(
                request=MagicMock(),
            )

            result = await list_zones()
            data = json.loads(result)

        assert data["status"] == "error"
        assert "连接" in data["message"]

    @pytest.mark.asyncio
    async def test_list_zones_generic_exception(self) -> None:
        """list_zones 未知异常时返回包含异常消息的错误响应。"""
        from claudeflare_mcp import list_zones

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_zones.side_effect = Exception("boom")

            result = await list_zones()
            data = json.loads(result)

        assert data["status"] == "error"
        assert "boom" in data["message"]

    @pytest.mark.asyncio
    async def test_list_dns_records_authentication_error(self) -> None:
        """list_dns_records Token 无效时返回包含"无效"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_dns_records

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_dns_records.side_effect = cloudflare.AuthenticationError(
                message="Invalid token",
                response=MagicMock(),
                body={},
            )

            result = await list_dns_records("zone-123")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_create_dns_record_zone_not_found(self) -> None:
        """create_dns_record Zone 不存在时返回含 zone_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import create_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.create_dns_record.side_effect = cloudflare.NotFoundError(
                message="Zone not found",
                response=MagicMock(),
                body={},
            )

            result = await create_dns_record("zone-bad", "A", "test.example.com", "1.2.3.4")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "zone-bad" in data["message"]

    @pytest.mark.asyncio
    async def test_create_dns_record_authentication_error(self) -> None:
        """create_dns_record Token 无效时返回包含"无效"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import create_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.create_dns_record.side_effect = cloudflare.AuthenticationError(
                message="Invalid token",
                response=MagicMock(),
                body={},
            )

            result = await create_dns_record("zone-123", "A", "test.example.com", "1.2.3.4")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_update_dns_record_not_found(self) -> None:
        """update_dns_record 记录不存在时返回含 record_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import update_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.update_dns_record.side_effect = cloudflare.NotFoundError(
                message="Record not found",
                response=MagicMock(),
                body={},
            )

            result = await update_dns_record("zone-123", "rec-bad", "9.9.9.9")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "rec-bad" in data["message"]

    @pytest.mark.asyncio
    async def test_update_dns_record_authentication_error(self) -> None:
        """update_dns_record Token 无效时返回包含"无效"的错误响应。"""
        import cloudflare

        from claudeflare_mcp import update_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.update_dns_record.side_effect = cloudflare.AuthenticationError(
                message="Invalid token",
                response=MagicMock(),
                body={},
            )

            result = await update_dns_record("zone-123", "rec-456", "9.9.9.9")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_dns_record_not_found(self) -> None:
        """delete_dns_record 记录不存在时返回含 record_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import delete_dns_record

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.delete_dns_record.side_effect = cloudflare.NotFoundError(
                message="Record not found",
                response=MagicMock(),
                body={},
            )

            result = await delete_dns_record("zone-123", "rec-bad")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "rec-bad" in data["message"]

    @pytest.mark.asyncio
    async def test_get_zone_settings_not_found(self) -> None:
        """get_zone_settings Zone 不存在时返回含 zone_id 的错误响应。"""
        import cloudflare

        from claudeflare_mcp import get_zone_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_zone_settings.side_effect = cloudflare.NotFoundError(
                message="Zone not found",
                response=MagicMock(),
                body={},
            )

            result = await get_zone_settings("zone-bad")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "zone-bad" in data["message"]

    @pytest.mark.asyncio
    async def test_get_zone_settings_generic_exception(self) -> None:
        """get_zone_settings 未知异常时返回包含异常消息的错误响应。"""
        from claudeflare_mcp import get_zone_settings

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.get_zone_settings.side_effect = Exception("boom")

            result = await get_zone_settings("zone-123")
            data = json.loads(result)

        assert data["status"] == "error"
        assert "boom" in data["message"]
