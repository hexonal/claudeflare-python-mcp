# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

claudeflare-python-mcp 是一个基于 **FastMCP 2.0** 的 Python MCP 服务器，封装了 Cloudflare 域名配置与常用 API 操作（DNS、Zone、WAF、Workers 等），供 Claude Code 直接调用。

架构模式完全参考 [hexonal/pg-python-mcp](https://github.com/hexonal/pg-python-mcp)。

---

## 核心技术栈

| 组件 | 包 | 说明 |
|------|-----|------|
| MCP 框架 | `fastmcp>=2.0.0` | `@mcp.tool()` 装饰器注册工具 |
| Cloudflare SDK | `cloudflare>=3.0` | 官方 SDK，同步/异步双客户端 |
| HTTP 客户端 | `httpx>=0.27.0` | SDK 底层依赖，也可直接用 |
| 构建后端 | `hatchling` | pyproject.toml 驱动 |
| 运行方式 | `uvx` | 从 Git 仓库直接运行，无需本地安装 |
| 代码质量 | `black` + `isort` + `mypy` | 行长 100，严格类型检查 |

---

## 包结构（参考 pg-python-mcp）

```
claudeflare_mcp/
├── __init__.py        # FastMCP 服务器初始化 + @mcp.tool() 工具注册
├── __main__.py        # 入口：mcp.run()
└── cf_handler.py      # CloudflareHandler 类，封装 SDK 调用
```

---

## 开发命令

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行服务器（本地调试）
python -m claudeflare_mcp

# 代码格式化
black --line-length 100 claudeflare_mcp/
isort claudeflare_mcp/

# 类型检查
mypy claudeflare_mcp/

# 运行测试
pytest

# 通过 uvx 从 Git 运行（生产方式）
uvx --from git+https://github.com/hexonal/claudeflare-python-mcp claudeflare-python-mcp
```

---

## Cloudflare SDK 使用模式

官方 SDK 文档：[cloudflare/cloudflare-python](https://github.com/cloudflare/cloudflare-python)

```python
import os
from cloudflare import AsyncCloudflare

# 客户端通过环境变量自动读取凭证
client = AsyncCloudflare(
    api_token=os.environ.get("CF_API_TOKEN"),
)

# 示例：列出 Zone
zones = await client.zones.list()

# 示例：创建 DNS 记录
record = await client.dns.records.create(
    zone_id="zone_id_here",
    type="A",
    name="example.com",
    content="1.2.3.4",
)
```

FastMCP 工具均使用 `AsyncCloudflare`，保持与框架的 async 一致性。

---

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `CF_API_KEY` | Cloudflare Global API Key（与 CF_API_EMAIL 配合使用） | 二选一 |
| `CF_API_EMAIL` | Cloudflare 账户邮箱（与 CF_API_KEY 配合使用） | 二选一 |
| `CF_API_TOKEN` | Cloudflare API Token（细粒度权限，与上两项互斥） | 二选一 |
| `CF_ACCOUNT_ID` | Cloudflare 账户 ID | 按功能需要 |
| `CF_ZONE_ID` | 默认操作的 Zone ID | 可选 |

---

## FastMCP 工具注册模式

每个工具遵循 pg-python-mcp 的统一响应结构：

```python
from fastmcp import FastMCP
import json

mcp = FastMCP("Cloudflare MCP Server")

@mcp.tool()
async def list_zones() -> str:
    """列出 Cloudflare 账户下的所有 Zone（域名）"""
    handler = CloudflareHandler()
    try:
        data = await handler.list_zones()
        return json.dumps({"status": "success", "data": data}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
```

响应格式固定为：`{"status": "success"|"error", "message": "...", "data": [...]}`

---

## pyproject.toml 关键配置

```toml
[project]
name = "claudeflare-python-mcp"
requires-python = ">=3.13"
dependencies = [
    "fastmcp>=2.0.0",
    "cloudflare>=3.0",
    "httpx>=0.27.0",
]

[project.scripts]
claudeflare-python-mcp = "claudeflare_mcp:mcp.run"

[tool.black]
line-length = 100
target-version = ["py38"]

[tool.mypy]
strict = true
warn_return_any = true
```

---

## .mcp.json 中注册此服务器

```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hexonal/claudeflare-python-mcp", "claudeflare-python-mcp"],
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

## 代码规范

- 方法行数 ≤ 50 行，参数 ≤ 4 个
- 注释独立成行，禁止行尾注释
- 工具函数必须有双语（中文/英文）docstring
- 所有 Cloudflare API 调用集中在 `cf_handler.py`，`__init__.py` 只做工具注册
