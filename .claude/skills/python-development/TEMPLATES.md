# Python 代码模板

## 目录
- [pyproject.toml 模板](#pyprojecttoml-模板)
- [Handler 模板](#handler-模板)
- [MCP 工具注册模板](#mcp-工具注册模板)
- [入口模板](#入口模板)
- [测试模板](#测试模板)

---

## pyproject.toml 模板

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claudeflare-python-mcp"
version = "1.0.0"
description = "Cloudflare 域名配置与常用 API 的 MCP 服务器"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.13"
dependencies = [
    "fastmcp>=2.0.0",
    "cloudflare>=3.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "black>=24.0.0",
    "isort>=5.13.0",
    "mypy>=1.10.0",
]

[project.scripts]
claudeflare-python-mcp = "claudeflare_mcp:run"

[tool.hatch.build.targets.wheel]
packages = ["claudeflare_mcp"]

[tool.black]
line-length = 100
target-version = ["py313"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unreachable = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## Handler 模板

```python
# claudeflare_mcp/cf_handler.py
"""
Cloudflare API 处理器模块。
Cloudflare API handler module.

@author {{通过 MCP git-config 自动获取}}
@date   {{通过 MCP mcp-datetime 自动获取}}
"""
import os

import cloudflare

# Python 3.12+ type 关键字定义类型别名（无需导入 TypeAlias）
type ZoneData = dict[str, object]
type DnsRecordData = dict[str, object]

# 环境变量
_CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
_CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")


def _require_token() -> str:
    """
    获取 API Token，未设置时抛出明确错误。
    Get API token, raise clear error if not set.
    """
    if not _CF_API_TOKEN:
        raise ValueError("CF_API_TOKEN 环境变量未设置")
    return _CF_API_TOKEN


class CloudflareHandler:
    """
    Cloudflare API 处理器，封装所有 SDK 调用。
    Cloudflare API handler that wraps all SDK calls.
    """

    def _get_client(self) -> cloudflare.AsyncCloudflare:
        """
        创建 Cloudflare 异步客户端。
        Create async Cloudflare client.
        """
        return cloudflare.AsyncCloudflare(api_token=_require_token())

    async def list_zones(self) -> list[ZoneData]:
        """
        列出账户下所有 Zone（域名）。
        List all Zones (domains) in the account.
        """
        async with self._get_client() as client:
            zones = await client.zones.list()
            return [
                {
                    "id": z.id,
                    "name": z.name,
                    "status": z.status,
                    "plan": z.plan.name if z.plan else None,
                }
                for z in zones
            ]

    async def list_dns_records(self, zone_id: str) -> list[DnsRecordData]:
        """
        列出指定 Zone 的所有 DNS 记录。
        List all DNS records for a zone.
        """
        async with self._get_client() as client:
            records = await client.dns.records.list(zone_id=zone_id)
            return [
                {
                    "id": r.id,
                    "type": r.type,
                    "name": r.name,
                    "content": r.content,
                    "ttl": r.ttl,
                    "proxied": r.proxied,
                }
                for r in records
            ]

    async def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 1,
    ) -> DnsRecordData:
        """
        创建 DNS 记录。
        Create a DNS record.
        """
        async with self._get_client() as client:
            record = await client.dns.records.create(
                zone_id=zone_id,
                type=record_type,  # type: ignore[arg-type]
                name=name,
                content=content,
                ttl=ttl,
            )
            return {
                "id": record.id,
                "type": record.type,
                "name": record.name,
                "content": record.content,
            }
```

---

## MCP 工具注册模板

```python
# claudeflare_mcp/__init__.py
"""
Cloudflare MCP 服务器，提供域名配置与常用 API 工具。
Cloudflare MCP server providing domain config and common API tools.

@author {{通过 MCP git-config 自动获取}}
@date   {{通过 MCP mcp-datetime 自动获取}}
"""
import json

import cloudflare
from fastmcp import FastMCP

from .cf_handler import CloudflareHandler

mcp = FastMCP("Cloudflare MCP Server")


def _success(data: object) -> str:
    """构建成功响应。Build success response."""
    return json.dumps({"status": "success", "data": data, "message": ""}, ensure_ascii=False)


def _error(message: str) -> str:
    """构建错误响应。Build error response."""
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
        return _error("CF_API_TOKEN 无效")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def list_dns_records(zone_id: str) -> str:
    """
    列出指定 Zone 的所有 DNS 记录。
    List all DNS records for a specific Zone.

    Args:
        zone_id: Zone ID，可通过 list_zones 获取。
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_dns_records(zone_id)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


@mcp.tool()
async def create_dns_record(
    zone_id: str,
    record_type: str,
    name: str,
    content: str,
    ttl: int = 1,
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
    """
    handler = CloudflareHandler()
    try:
        data = await handler.create_dns_record(zone_id, record_type, name, content, ttl)
        return _success(data)
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except Exception as exc:
        return _error(str(exc))


def run() -> None:
    """MCP 服务器入口。MCP server entry point."""
    mcp.run()
```

---

## 入口模板

```python
# claudeflare_mcp/__main__.py
"""
MCP 服务器直接运行入口。
Direct execution entry point for the MCP server.
"""
from claudeflare_mcp import run

if __name__ == "__main__":
    run()
```

---

## 测试模板

```python
# tests/test_tools.py
"""
MCP 工具函数集成测试。
Integration tests for MCP tool functions.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest


class TestListZones:
    """list_zones 工具测试。"""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CF_API_TOKEN", "test-token")

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        """成功场景：返回 Zone 列表。"""
        from claudeflare_mcp import list_zones

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_zones.return_value = [
                {"id": "z1", "name": "example.com", "status": "active"}
            ]

            result = await list_zones()
            data = json.loads(result)

        assert data["status"] == "success"
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_auth_error(self) -> None:
        """认证失败：返回错误响应。"""
        import cloudflare

        from claudeflare_mcp import list_zones

        with patch("claudeflare_mcp.CloudflareHandler") as mock_cls:
            mock_handler = AsyncMock()
            mock_cls.return_value = mock_handler
            mock_handler.list_zones.side_effect = cloudflare.AuthenticationError(
                message="Invalid", response=None, body={}  # type: ignore[arg-type]
            )

            result = await list_zones()
            data = json.loads(result)

        assert data["status"] == "error"
        assert "无效" in data["message"]
```
