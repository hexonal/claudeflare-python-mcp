# claudeflare-python-mcp

基于 **FastMCP 2.0** 的 Python MCP 服务器，封装了 Cloudflare 域名配置与常用 API 操作（DNS、Zone、WAF、Workers 等），供 Claude Code 直接调用。

架构模式参考 [hexonal/pg-python-mcp](https://github.com/hexonal/pg-python-mcp)。

---

## 快速开始

在 `.mcp.json` 中添加以下配置，重启 Claude Code 即可使用：

```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hexonal/claudeflare-python-mcp",
        "claudeflare-python-mcp"
      ],
      "env": {
        "CF_API_KEY": "<your-global-api-key>",
        "CF_API_EMAIL": "<your-cloudflare-email>",
        "CF_ACCOUNT_ID": "<your-account-id>"
      }
    }
  }
}
```

> 也支持 API Token 认证：将 `CF_API_KEY` + `CF_API_EMAIL` 替换为单个 `CF_API_TOKEN`。

---

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `CF_API_KEY` | Cloudflare Global API Key（与 `CF_API_EMAIL` 配合使用） | 二选一 |
| `CF_API_EMAIL` | Cloudflare 账户邮箱（与 `CF_API_KEY` 配合使用） | 二选一 |
| `CF_API_TOKEN` | Cloudflare API Token（细粒度权限，与上两项互斥） | 二选一 |
| `CF_ACCOUNT_ID` | Cloudflare 账户 ID | 按功能需要 |

---

## 可用工具

### Zone

| 工具 | 说明 |
|------|------|
| `list_zones` | 列出账户下所有域名 |
| `get_zone_settings` | 获取 Zone 的安全和性能配置 |

### DNS

| 工具 | 说明 |
|------|------|
| `list_dns_records` | 列出指定 Zone 的所有 DNS 记录 |
| `create_dns_record` | 创建 DNS 记录（支持 `proxied` 小黄云开关） |
| `update_dns_record` | 更新 DNS 记录内容（支持切换 `proxied` 状态） |
| `delete_dns_record` | 删除 DNS 记录 |
| `get_dnssec` | 获取 DNSSEC 状态 |
| `get_dns_settings` | 获取 DNS 基础设置 |

### 缓存

| 工具 | 说明 |
|------|------|
| `purge_cache` | 清除缓存（全部、按 URL 或按 Cache-Tag） |
| `get_cache_settings` | 获取缓存配置 |

### 性能

| 工具 | 说明 |
|------|------|
| `get_speed_settings` | 获取性能优化配置（Brotli、HTTP/2 等） |

### 安全

| 工具 | 说明 |
|------|------|
| `list_firewall_rules` | 列出防火墙访问规则 |
| `get_security_settings` | 获取安全配置（安全级别、WAF 等） |

### SSL/TLS

| 工具 | 说明 |
|------|------|
| `get_ssl_settings` | 获取 SSL/TLS 通用设置 |
| `list_ssl_certificates` | 列出 SSL 证书包 |
| `list_custom_hostnames` | 列出自定义主机名 |
| `create_custom_hostname` | 创建自定义主机名（HTTP DV 证书） |

### 邮件路由

| 工具 | 说明 |
|------|------|
| `get_email_routing` | 获取邮件路由设置 |
| `list_email_routing_rules` | 列出邮件路由规则 |

### 分析

| 工具 | 说明 |
|------|------|
| `get_zone_analytics` | 获取最近 24 小时流量分析 |

### Workers AI

| 工具 | 说明 |
|------|------|
| `list_ai_models` | 列出可用 Workers AI 模型 |
| `run_ai` | 调用 Workers AI 模型执行推理 |

### Workers

| 工具 | 说明 |
|------|------|
| `list_workers` | 列出账户下所有 Workers 脚本 |
| `list_worker_routes` | 列出 Zone 的 Worker 路由规则 |
| `get_worker` | 获取指定 Worker 脚本的元数据 |

---

## 技术栈

| 组件 | 包 | 说明 |
|------|-----|------|
| MCP 框架 | `fastmcp>=2.0.0` | `@mcp.tool()` 装饰器注册工具 |
| Cloudflare SDK | `cloudflare>=3.0` | 官方异步 SDK |
| HTTP 客户端 | `httpx>=0.27.0` | 直接调用部分未封装端点 |
| Python | `>=3.13` | 原生 `type` 语法，严格类型检查 |

---

## 本地开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行服务器
python -m claudeflare_mcp

# 代码格式化
black --line-length 100 claudeflare_mcp/
isort claudeflare_mcp/

# 类型检查
mypy --strict claudeflare_mcp/

# 单元测试
uv run pytest tests/ -v

# 集成测试（只读）
export CF_API_KEY="..."
export CF_API_EMAIL="..."
export CF_ACCOUNT_ID="..."
uv run pytest tests/test_integration.py -v -k "not Write"

# 集成测试（含写操作）
RUN_WRITE_TESTS=1 uv run pytest tests/test_integration.py -v
```

---

## 项目结构

```
claudeflare_mcp/
├── __init__.py     # FastMCP 服务器 + @mcp.tool() 工具注册
├── __main__.py     # 入口：mcp.run()
└── cf_handler.py   # CloudflareHandler 类，封装所有 SDK 调用
tests/
├── conftest.py
├── test_handler.py
├── test_tools.py
├── test_new_tools.py
└── test_integration.py
```
