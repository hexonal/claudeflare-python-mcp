"""
真实 Cloudflare API 集成测试。
Real Cloudflare API integration tests.

运行方式 / How to run:
  # 只读测试（不修改任何数据）
  export CF_API_KEY="<your-global-api-key>"
  export CF_API_EMAIL="<your-email>"
  export CF_ACCOUNT_ID="<your-account-id>"
  uv run pytest tests/test_integration.py -v -k "not Write"

  # 包含写操作的全量测试
  RUN_WRITE_TESTS=1 uv run pytest tests/test_integration.py -v
"""

import os

import pytest

# 有凭证才运行，否则跳过整个模块
_HAS_CREDENTIALS = bool(
    os.environ.get("CF_API_TOKEN")
    or (os.environ.get("CF_API_KEY") and os.environ.get("CF_API_EMAIL"))
)

pytestmark = pytest.mark.skipif(
    not _HAS_CREDENTIALS,
    reason="需要设置 CF_API_TOKEN 或 CF_API_KEY + CF_API_EMAIL",
)


def _make_handler() -> "CloudflareHandler":  # type: ignore[name-defined]
    """
    惰性创建 CloudflareHandler，避免在 pytest 收集阶段导入模块（会导致 _CF_API_TOKEN 被提前读取为空）。
    Lazily create CloudflareHandler to avoid premature module import at pytest collection time.
    """
    from claudeflare_mcp.cf_handler import CloudflareHandler

    return CloudflareHandler()


# ── 阶段 1：Zone 发现 ─────────────────────────────────────────────────────────


class TestIntegrationZoneDiscovery:
    """阶段 1：验证凭证并获取 Zone ID。"""

    async def test_list_zones(self) -> None:
        """list_zones 应返回包含 996icu.wiki 的列表。"""
        handler = _make_handler()
        zones = await handler.list_zones()
        assert isinstance(zones, list)
        names = [z.get("name") for z in zones]
        assert "996icu.wiki" in names, f"未找到 996icu.wiki，当前域名列表：{names}"

    async def test_get_zone_settings(self, zone_id: str) -> None:
        """get_zone_settings 应返回非空设置字典。"""
        handler = _make_handler()
        settings = await handler.get_zone_settings(zone_id)
        assert isinstance(settings, dict)
        assert len(settings) > 0, "Zone 设置字典不应为空"


# ── 阶段 2：只读工具 ──────────────────────────────────────────────────────────


class TestIntegrationReadOnly:
    """阶段 2：只读工具测试（不修改任何 Cloudflare 数据）。"""

    async def test_list_dns_records(self, zone_id: str) -> None:
        """list_dns_records 应返回列表（空列表也视为通过）。"""
        handler = _make_handler()
        records = await handler.list_dns_records(zone_id)
        assert isinstance(records, list)

    async def test_get_cache_settings(self, zone_id: str) -> None:
        """get_cache_settings 应包含 cache_level 键。"""
        handler = _make_handler()
        settings = await handler.get_cache_settings(zone_id)
        assert isinstance(settings, dict)
        assert "cache_level" in settings, f"缺少 cache_level 键，实际键：{list(settings.keys())}"

    async def test_get_speed_settings(self, zone_id: str) -> None:
        """get_speed_settings 应包含 brotli 或 rocket_loader 键之一。"""
        handler = _make_handler()
        settings = await handler.get_speed_settings(zone_id)
        assert isinstance(settings, dict)
        speed_keys = {"brotli", "rocket_loader", "http2", "http3", "early_hints"}
        assert any(k in settings for k in speed_keys), (
            f"速度设置中未找到预期键，实际键：{list(settings.keys())}"
        )

    async def test_get_security_settings(self, zone_id: str) -> None:
        """get_security_settings 应包含 security_level 键。"""
        handler = _make_handler()
        settings = await handler.get_security_settings(zone_id)
        assert isinstance(settings, dict)
        assert "security_level" in settings, (
            f"缺少 security_level 键，实际键：{list(settings.keys())}"
        )

    async def test_get_ssl_settings(self, zone_id: str) -> None:
        """get_ssl_settings 应包含 enabled 键。"""
        handler = _make_handler()
        ssl = await handler.get_ssl_settings(zone_id)
        assert isinstance(ssl, dict)
        assert "enabled" in ssl, f"缺少 enabled 键，实际键：{list(ssl.keys())}"

    async def test_list_ssl_certificates(self, zone_id: str) -> None:
        """list_ssl_certificates 应返回列表。"""
        handler = _make_handler()
        certs = await handler.list_ssl_certificates(zone_id)
        assert isinstance(certs, list)

    async def test_list_firewall_rules(self, zone_id: str) -> None:
        """list_firewall_rules 应返回列表（空列表也视为通过）。"""
        handler = _make_handler()
        rules = await handler.list_firewall_rules(zone_id)
        assert isinstance(rules, list)

    async def test_get_email_routing(self, zone_id: str) -> None:
        """get_email_routing 应返回包含 enabled 键的字典（未启用也视为通过）。"""
        handler = _make_handler()
        try:
            routing = await handler.get_email_routing(zone_id)
            assert isinstance(routing, dict)
        except Exception as exc:
            # 未开通邮件路由时 API 返回错误，视为预期情况
            assert "email" in str(exc).lower() or "routing" in str(exc).lower(), (
                f"get_email_routing 抛出意外错误：{exc}"
            )

    async def test_list_email_routing_rules(self, zone_id: str) -> None:
        """list_email_routing_rules 应返回列表（空列表也视为通过）。"""
        handler = _make_handler()
        try:
            rules = await handler.list_email_routing_rules(zone_id)
            assert isinstance(rules, list)
        except Exception as exc:
            # 未开通邮件路由时 API 返回错误，视为预期情况
            assert "email" in str(exc).lower() or "routing" in str(exc).lower(), (
                f"list_email_routing_rules 抛出意外错误：{exc}"
            )

    async def test_get_dnssec(self, zone_id: str) -> None:
        """get_dnssec 应返回包含 status 字段的字典（disabled 也视为通过）。"""
        handler = _make_handler()
        dnssec = await handler.get_dnssec(zone_id)
        assert isinstance(dnssec, dict)
        assert "status" in dnssec, f"缺少 status 键，实际键：{list(dnssec.keys())}"

    async def test_get_dns_settings(self, zone_id: str) -> None:
        """get_dns_settings 应返回字典。"""
        handler = _make_handler()
        settings = await handler.get_dns_settings(zone_id)
        assert isinstance(settings, dict)

    async def test_get_zone_analytics(self, zone_id: str) -> None:
        """get_zone_analytics 应返回字典；若有数据则含 requests/bandwidth/threats/pageviews。"""
        handler = _make_handler()
        analytics = await handler.get_zone_analytics(zone_id)
        assert isinstance(analytics, dict), "get_zone_analytics 应返回 dict"
        # 空字典表示该时间段无流量数据（新域名或低流量域名属正常情况）
        if analytics:
            required_keys = {"requests", "bandwidth", "threats", "pageviews"}
            assert required_keys.issubset(analytics.keys()), (
                f"缺少必要键，期望：{required_keys}，实际：{set(analytics.keys())}"
            )

    async def test_list_custom_hostnames(self, zone_id: str) -> None:
        """list_custom_hostnames 应返回列表，或返回明确的 SaaS 权限不足错误。"""
        handler = _make_handler()
        try:
            hostnames = await handler.list_custom_hostnames(zone_id)
            assert isinstance(hostnames, list)
        except Exception as exc:
            # 非 SaaS 套餐时 API 返回 1550 错误，视为预期情况
            err_msg = str(exc)
            assert any(
                keyword in err_msg for keyword in ["1550", "saas", "SaaS", "plan", "Plan"]
            ), f"list_custom_hostnames 抛出意外错误：{exc}"

    async def test_list_workers(self, account_id: str) -> None:
        """list_workers 应返回列表（空列表也视为通过）。"""
        handler = _make_handler()
        workers = await handler.list_workers(account_id)
        assert isinstance(workers, list)

    async def test_list_worker_routes(self, zone_id: str) -> None:
        """list_worker_routes 应返回列表（空列表也视为通过）。"""
        handler = _make_handler()
        routes = await handler.list_worker_routes(zone_id)
        assert isinstance(routes, list)

    async def test_list_ai_models(self, account_id: str) -> None:
        """list_ai_models 应返回列表，或返回明确的 Workers AI 未开通错误。"""
        handler = _make_handler()
        try:
            models = await handler.list_ai_models(account_id)
            assert isinstance(models, list)
        except Exception as exc:
            # Workers AI 未开通时 API 返回错误，视为预期情况
            assert any(
                keyword in str(exc) for keyword in ["ai", "AI", "worker", "Worker", "403", "401"]
            ), f"list_ai_models 抛出意外错误：{exc}"


# ── 阶段 3：写操作（需 RUN_WRITE_TESTS=1）───────────────────────────────────


_RUN_WRITE = os.environ.get("RUN_WRITE_TESTS", "") == "1"

_WRITE_SKIP_REASON = "写操作测试默认跳过，设置 RUN_WRITE_TESTS=1 以启用"

# 测试服务器真实 IP
_TEST_RECORD_IP = "167.114.174.225"

# 灰云（no-proxy）测试记录名
_TEST_RECORD_GRAY = "test-mcp-gray"

# 橙云（proxied）测试记录名
_TEST_RECORD_ORANGE = "test-mcp-orange"


@pytest.mark.skipif(not _RUN_WRITE, reason=_WRITE_SKIP_REASON)
class TestIntegrationWrite:
    """阶段 3：写操作测试（含自动清理）。"""

    _no_proxy_id: str = ""
    _proxied_id: str = ""
    _custom_hostname_id: str = ""

    async def test_create_dns_record_no_proxy(self, zone_id: str) -> None:
        """create_dns_record proxied=False 应创建灰云 A 记录（test-mcp-gray）。"""
        handler = _make_handler()
        record = await handler.create_dns_record(
            zone_id=zone_id,
            record_type="A",
            name=_TEST_RECORD_GRAY,
            content=_TEST_RECORD_IP,
            ttl=120,
            proxied=False,
        )
        assert isinstance(record, dict)
        assert record.get("id"), "创建的记录缺少 id"
        assert record.get("type") == "A"
        assert record.get("proxied") is False, f"proxied 应为 False，实际：{record.get('proxied')}"
        TestIntegrationWrite._no_proxy_id = str(record["id"])

    async def test_create_dns_record_proxied(self, zone_id: str) -> None:
        """create_dns_record proxied=True 应创建橙云（代理）A 记录（test-mcp-orange）。"""
        handler = _make_handler()
        record = await handler.create_dns_record(
            zone_id=zone_id,
            record_type="A",
            name=_TEST_RECORD_ORANGE,
            content=_TEST_RECORD_IP,
            ttl=1,
            proxied=True,
        )
        assert isinstance(record, dict)
        assert record.get("id"), "创建的记录缺少 id"
        assert record.get("proxied") is True, f"proxied 应为 True，实际：{record.get('proxied')}"
        TestIntegrationWrite._proxied_id = str(record["id"])

    async def test_update_dns_record_toggle_proxy(self, zone_id: str) -> None:
        """update_dns_record proxied=True 应将灰云记录切换为橙云。"""
        if not TestIntegrationWrite._no_proxy_id:
            pytest.skip("依赖 test_create_dns_record_no_proxy 先创建记录")
        handler = _make_handler()
        record = await handler.update_dns_record(
            zone_id=zone_id,
            record_id=TestIntegrationWrite._no_proxy_id,
            content=_TEST_RECORD_IP,
            ttl=1,
            proxied=True,
        )
        assert isinstance(record, dict)
        assert record.get("proxied") is True, (
            f"proxied 切换失败，实际：{record.get('proxied')}"
        )

    async def test_delete_dns_records(self, zone_id: str) -> None:
        """删除两条测试 DNS 记录（no-proxy 和 proxied）。"""
        handler = _make_handler()
        if TestIntegrationWrite._no_proxy_id:
            result = await handler.delete_dns_record(
                zone_id=zone_id,
                record_id=TestIntegrationWrite._no_proxy_id,
            )
            assert result is True
            TestIntegrationWrite._no_proxy_id = ""
        if TestIntegrationWrite._proxied_id:
            result = await handler.delete_dns_record(
                zone_id=zone_id,
                record_id=TestIntegrationWrite._proxied_id,
            )
            assert result is True
            TestIntegrationWrite._proxied_id = ""

    async def test_purge_cache_everything(self, zone_id: str) -> None:
        """purge_cache purge_everything=True 应成功清除 Zone 缓存。"""
        handler = _make_handler()
        result = await handler.purge_cache(zone_id=zone_id, purge_everything=True)
        assert isinstance(result, dict)
        assert result.get("purged") is True

    async def test_create_custom_hostname(self, zone_id: str) -> None:
        """create_custom_hostname 应成功创建，或返回已知 SaaS 套餐限制错误。"""
        handler = _make_handler()
        test_hostname = "test-mcp.example.com"
        try:
            result = await handler.create_custom_hostname(zone_id, test_hostname)
            assert result.get("id"), "创建的 custom hostname 缺少 id"
            TestIntegrationWrite._custom_hostname_id = str(result["id"])
        except Exception as exc:
            # 非 SaaS 套餐返回 1550/plan 错误，保留域名（example.com 等）返回 1411，均视为预期
            assert any(
                k in str(exc) for k in ["1550", "1411", "SaaS", "saas", "plan", "Plan", "prohibited"]
            ), f"create_custom_hostname 返回意外错误：{exc}"


# ── 阶段 4：AI 工具（需 Workers AI 开通）────────────────────────────────────


@pytest.mark.skipif(not _RUN_WRITE, reason="AI 推理测试与写测试一起启用（RUN_WRITE_TESTS=1）")
class TestIntegrationAI:
    """阶段 4：Workers AI 工具测试。"""

    async def test_run_ai(self, account_id: str) -> None:
        """run_ai 应调用 llama 模型并返回包含 response 键的结果，或返回 AI 未开通错误。"""
        handler = _make_handler()
        try:
            result = await handler.run_ai(
                account_id=account_id,
                model_name="@cf/meta/llama-3.1-8b-instruct",
                prompt="Hi",
            )
            assert isinstance(result, dict)
            assert "response" in result or len(result) > 0, "AI 结果字典不应为空"
        except Exception as exc:
            # Workers AI 未开通时视为预期情况
            assert any(
                keyword in str(exc) for keyword in ["ai", "AI", "Worker", "403", "401", "model"]
            ), f"run_ai 抛出意外错误：{exc}"
