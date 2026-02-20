# Python 详细规范参考

## 目录
- [Handler 层规范](#handler-层规范)
- [类型系统](#类型系统)
- [错误处理详解](#错误处理详解)
- [测试规范](#测试规范)
- [Cloudflare SDK 集成模式](#cloudflare-sdk-集成模式)

---

## Handler 层规范

### 基础 Handler 结构

Handler 类封装所有 Cloudflare SDK 调用，工具函数（`__init__.py`）只负责编排和响应格式化。

```python
# cf_handler.py
# Python 3.13：无需 from __future__ import annotations
import os

import cloudflare

CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")


class CloudflareHandler:
    """
    Cloudflare API 处理器，封装所有 SDK 调用。
    Cloudflare API handler that wraps all SDK calls.
    """

    def _get_client(self) -> cloudflare.AsyncCloudflare:
        """
        创建并返回 Cloudflare 异步客户端。
        Create and return an async Cloudflare client.
        """
        if not CF_API_TOKEN:
            raise ValueError("CF_API_TOKEN 环境变量未设置")
        return cloudflare.AsyncCloudflare(api_token=CF_API_TOKEN)

    async def list_zones(self) -> list[dict[str, object]]:
        """
        列出账户下所有 Zone。
        List all zones in the account.
        """
        async with self._get_client() as client:
            zones = await client.zones.list()
            return [
                {"id": z.id, "name": z.name, "status": z.status}
                for z in zones
            ]
```

### Handler 方法命名约定

```python
# 列表操作：list_*
async def list_zones(self) -> list[dict[str, object]]: ...
async def list_dns_records(self, zone_id: str) -> list[dict[str, object]]: ...

# 获取单个：get_*
async def get_zone(self, zone_id: str) -> dict[str, object]: ...

# 创建：create_*
async def create_dns_record(self, zone_id: str, ...) -> dict[str, object]: ...

# 更新：update_*
async def update_dns_record(self, zone_id: str, record_id: str, ...) -> dict[str, object]: ...

# 删除：delete_*
async def delete_dns_record(self, zone_id: str, record_id: str) -> bool: ...
```

---

## 类型系统

### 类型别名定义

```python
# Python 3.12+ 新语法：type 关键字，无需导入 TypeAlias
type ZoneData = dict[str, object]
type DnsRecordData = dict[str, object]
type ApiResponse = dict[str, object | list[object] | None]
```

### 响应构建函数

```python
import json


def _success(data: object) -> str:
    """构建成功响应 JSON。Build success response JSON."""
    return json.dumps(
        {"status": "success", "data": data, "message": ""},
        ensure_ascii=False,
    )


def _error(message: str) -> str:
    """构建错误响应 JSON。Build error response JSON."""
    return json.dumps(
        {"status": "error", "data": None, "message": message},
        ensure_ascii=False,
    )
```

### 环境变量安全读取

```python
def _require_env(name: str) -> str:
    """
    读取必须存在的环境变量，缺失时抛出明确错误。
    Read required env var, raise clear error if missing.
    """
    value = os.environ.get(name, "")
    if not value:
        raise ValueError(f"环境变量 {name} 未设置，请检查 MCP 配置的 env 字段")
    return value
```

---

## 错误处理详解

### Cloudflare SDK 异常类型

```python
import cloudflare

# 常见异常类型
cloudflare.APIConnectionError    # 网络连接失败
cloudflare.AuthenticationError   # API Token 无效（401）
cloudflare.PermissionDeniedError # 权限不足（403）
cloudflare.NotFoundError         # 资源不存在（404）
cloudflare.RateLimitError        # 请求频率限制（429）
cloudflare.APIStatusError        # 其他 API 错误（基类）
```

### 分层错误处理

```python
@mcp.tool()
async def create_dns_record(
    zone_id: str,
    record_type: str,
    name: str,
    content: str,
) -> str:
    """
    创建 DNS 记录。Create a DNS record.
    """
    handler = CloudflareHandler()
    try:
        result = await handler.create_dns_record(zone_id, record_type, name, content)
        return _success(result)
    except cloudflare.AuthenticationError:
        return _error("CF_API_TOKEN 无效，请检查 Token 是否正确")
    except cloudflare.NotFoundError:
        return _error(f"Zone {zone_id} 不存在")
    except cloudflare.APIConnectionError as exc:
        return _error(f"连接 Cloudflare API 失败: {exc}")
    except Exception as exc:
        return _error(str(exc))
```

---

## 测试规范

### 测试文件结构

```python
# tests/test_handler.py
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCloudflareHandler:
    """CloudflareHandler 单元测试。"""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """设置测试环境变量。"""
        monkeypatch.setenv("CF_API_TOKEN", "test-token-xxx")
        monkeypatch.setenv("CF_ACCOUNT_ID", "test-account-id")

    @pytest.mark.asyncio
    async def test_list_zones_success(self) -> None:
        """测试 list_zones 成功场景。"""
        mock_zone = MagicMock()
        mock_zone.id = "zone-123"
        mock_zone.name = "example.com"
        mock_zone.status = "active"

        with patch("cloudflare.AsyncCloudflare") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.zones.list.return_value = [mock_zone]

            from claudeflare_mcp.cf_handler import CloudflareHandler
            handler = CloudflareHandler()
            result = await handler.list_zones()

        assert len(result) == 1
        assert result[0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_list_zones_auth_error(self) -> None:
        """测试 list_zones 认证失败场景。"""
        import cloudflare

        with patch("cloudflare.AsyncCloudflare") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.zones.list.side_effect = cloudflare.AuthenticationError(
                message="Invalid token", response=MagicMock(), body={}
            )

            from claudeflare_mcp.cf_handler import CloudflareHandler
            handler = CloudflareHandler()
            with pytest.raises(cloudflare.AuthenticationError):
                await handler.list_zones()
```

### pytest 配置

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 运行单个测试

```bash
# 运行单个测试类
pytest tests/test_handler.py::TestCloudflareHandler -v

# 运行单个测试方法
pytest tests/test_handler.py::TestCloudflareHandler::test_list_zones_success -v

# 覆盖率报告
pytest --cov=claudeflare_mcp --cov-report=term-missing
```

---

## Cloudflare SDK 集成模式

### 异步上下文管理器模式（推荐）

```python
# 每次调用创建新客户端（简单，适合 MCP 工具）
async with cloudflare.AsyncCloudflare(api_token=token) as client:
    zones = await client.zones.list()
```

### 自动分页

```python
# SDK 内置分页迭代器，自动处理多页
async for zone in await client.zones.list():
    process(zone)

# 转为列表（注意内存，大量数据时谨慎）
zones = [z async for z in await client.zones.list()]
```

### 主要 API 命名空间

| 功能 | SDK 路径 |
|------|---------|
| Zone 管理 | `client.zones` |
| DNS 记录 | `client.dns.records` |
| WAF 规则集 | `client.rulesets` |
| 防火墙规则 | `client.firewall.rules` |
| Workers | `client.workers.scripts` |
| R2 存储 | `client.r2.buckets` |
| SSL 证书 | `client.ssl.certificate_packs` |
| 页面规则 | `client.page_rules` |
| 缓存设置 | `client.cache` |
