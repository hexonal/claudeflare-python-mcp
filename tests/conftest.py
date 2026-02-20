"""
pytest 配置与共享 fixture。
pytest configuration and shared fixtures.
"""

import os

import pytest
import pytest_asyncio

# 测试目标域名
_TARGET_DOMAIN = "996icu.wiki"

# 测试使用的 Cloudflare Account ID
_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "a682f60bf96deede25b5779e7254ffb0")


@pytest_asyncio.fixture(scope="session")
async def zone_id() -> str:
    """
    Session 级 fixture：调用 list_zones 获取 baoluo.eu.org 的 Zone ID。
    Session-level fixture: calls list_zones once to get Zone ID for baoluo.eu.org.
    """
    # 延迟导入，避免在 pytest 收集阶段过早加载模块导致环境变量读取时机错误
    from claudeflare_mcp.cf_handler import CloudflareHandler

    handler = CloudflareHandler()
    zones = await handler.list_zones()
    for zone in zones:
        if zone.get("name") == _TARGET_DOMAIN:
            return str(zone["id"])
    raise RuntimeError(f"未找到域名 {_TARGET_DOMAIN}，请确认账户下存在该域名")


@pytest.fixture(scope="session")
def account_id() -> str:
    """
    Session 级 fixture：返回测试用的 Cloudflare Account ID。
    Session-level fixture: returns the Cloudflare Account ID for testing.
    """
    return _ACCOUNT_ID
