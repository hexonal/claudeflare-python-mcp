---
name: python-development
description: |
  编写符合 Python 3.13+ 最佳实践的 MCP 服务器代码，使用 FastMCP 2.0 框架。
  适用于：创建/修改 .py 文件、编写 MCP 工具函数、实现 Handler 处理器、
  配置 pyproject.toml、处理 Cloudflare SDK 集成。
  触发关键词：Python、FastMCP、MCP 工具、Handler、pyproject、uvx、cloudflare SDK。
  ⚠️ 编写 Python 代码时必须严格遵守此规范的强制规则，违反将导致代码审查不通过。
---

# Python Development Skill

Python 3.13+ MCP 服务器开发规范，专注于 FastMCP 2.0 + Cloudflare SDK 集成。

## ⚠️ 规范约束

本规范包含以下级别的规则，编码时必须遵守：

- 🔴 **强制规则**：违反将导致代码审查不通过或运行时错误
- 🟡 **推荐规则**：强烈建议遵守，特殊情况可例外
- 🟢 **可选规则**：根据场景选择使用

---

## 快速参考

**详细规范**: 见 [REFERENCE.md](REFERENCE.md)
**代码模板**: 见 [TEMPLATES.md](TEMPLATES.md)

---

## 核心原则

| 原则 | 要求 |
|------|------|
| **YAGNI** | 只实现当前需要的功能 |
| **KISS** | Handler → Tool 两层架构，禁止过度抽象 |
| **单一职责** | Handler 负责 API 调用，Tool 函数负责编排和响应格式化 |

---

## 🔴 强制规则

### 代码行数限制

| 类型 | 最大行数 |
|------|----------|
| 函数/方法 | 50 行 |
| 文件 | 500 行 |

### 类型注解（必须通过 mypy --strict）

Python 3.13 无需 `from __future__ import annotations`，直接使用新语法：

```python
# ✅ 正确：完整类型注解（3.13 原生语法）
async def list_zones(account_id: str | None = None) -> str: ...

# ✅ 正确：type 关键字定义类型别名（3.12+）
type ZoneData = dict[str, object]
type DnsRecordData = dict[str, object]

# ✅ 正确：使用具体类型
def _build_response(data: list[dict[str, object]]) -> str: ...

# ❌ 禁止：缺少类型注解
async def list_zones(account_id=None): ...

# ❌ 禁止：使用 Any
from typing import Any
def process(data: Any) -> Any: ...  # 严禁！

# ❌ 禁止：Python 3.13 中的旧式写法（无需兼容旧版本）
from __future__ import annotations   # 不再需要
from typing import Optional, List, Dict  # 使用 X | None、list、dict 替代
```

### 注释规范

```python
# ✅ 正确：注释独立成行
# 列出所有 Zone
zones = await client.zones.list()

# ❌ 禁止：行尾注释
zones = await client.zones.list()  # 列出 Zone
```

### Docstring 必须（双语）

```python
async def list_zones() -> str:
    """
    列出 Cloudflare 账户下的所有 Zone（域名）。
    List all Zones (domains) in the Cloudflare account.
    """
```

---

## 项目结构

```
claudeflare_mcp/
├── __init__.py        # FastMCP 服务器 + @mcp.tool() 注册
├── __main__.py        # 入口：mcp.run()
└── cf_handler.py      # CloudflareHandler 类，封装 SDK 调用
tests/
├── test_handler.py
└── test_tools.py
pyproject.toml
```

---

## FastMCP 工具注册模式

### 工具函数标准结构

```python
@mcp.tool()
async def list_zones() -> str:
    """
    列出账户下所有 Zone。
    List all zones in the account.
    """
    handler = CloudflareHandler()
    try:
        data = await handler.list_zones()
        return json.dumps(
            {"status": "success", "data": data},
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps(
            {"status": "error", "message": str(exc)},
            ensure_ascii=False,
        )
```

### 响应格式（固定结构）

```python
# 成功
{"status": "success", "data": [...], "message": ""}

# 错误
{"status": "error", "message": "错误描述", "data": None}
```

---

## 命名规范速查

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | snake_case | `cf_handler`, `dns_tools` |
| 类名 | PascalCase | `CloudflareHandler` |
| 函数/方法 | snake_case | `list_zones`, `create_dns_record` |
| 常量 | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT`, `MAX_RETRIES` |
| 私有方法 | `_` 前缀 | `_build_response`, `_get_client` |
| 类型别名 | PascalCase | `ZoneList`, `DnsRecord` |

---

## 环境变量规范

```python
import os

# ✅ 正确：有默认值或明确处理缺失
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
if not CF_API_TOKEN:
    raise ValueError("CF_API_TOKEN environment variable is required")

# ❌ 禁止：直接 os.environ[] 不处理 KeyError
token = os.environ["CF_API_TOKEN"]  # 崩溃时错误信息不友好
```

---

## 错误处理规范

```python
# ✅ 正确：捕获具体异常，转换为统一响应
async def create_dns_record(zone_id: str, name: str, content: str) -> str:
    handler = CloudflareHandler()
    try:
        result = await handler.create_dns_record(zone_id, name, content)
        return json.dumps({"status": "success", "data": result}, ensure_ascii=False)
    except cloudflare.APIConnectionError as exc:
        return json.dumps({"status": "error", "message": f"连接失败: {exc}"}, ensure_ascii=False)
    except cloudflare.AuthenticationError:
        return json.dumps({"status": "error", "message": "API Token 无效"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)
```

---

## 禁用功能清单

- `Any` 类型 - 任何场景禁止
- 行尾注释 - 所有注释必须独立成行
- `os.environ[]` 直接访问 - 使用 `os.environ.get()` 并处理缺失
- 同步 HTTP 调用在 async 函数中 - 必须使用 `await`
- 裸 `except:` - 必须指定异常类型

---

## 常用命令

```bash
# 安装开发依赖
pip install -e ".[dev]"
# 或
uv pip install -e ".[dev]"

# 格式化
black --line-length 100 .
isort .

# 类型检查
mypy --strict claudeflare_mcp/

# 运行测试
pytest
pytest tests/test_handler.py::TestCloudflareHandler::test_list_zones -v

# 运行 MCP 服务器（本地调试）
python -m claudeflare_mcp

# uvx 方式运行（生产）
uvx --from git+https://github.com/hexonal/claudeflare-python-mcp claudeflare-python-mcp
```

---

## MCP 工具集成

| 工具 | 用途 |
|------|------|
| sequential-thinking | 架构设计、复杂问题分析 |
| context7 | FastMCP/cloudflare SDK 官方文档查询 |
| deepwiki | Python 生态、开源库文档 |
| git-config | Git 用户信息获取 |
| mcp-datetime | 时间戳生成 |

---

## 检查清单

- [ ] 函数 < 50 行
- [ ] 所有参数和返回值有类型注解
- [ ] `mypy --strict` 通过
- [ ] 无 `Any` 类型
- [ ] 无行尾注释
- [ ] 公共函数有双语 docstring
- [ ] 错误处理返回统一 JSON 响应格式
- [ ] `black` 和 `isort` 通过

---

## 参考文档

- **[REFERENCE.md](REFERENCE.md)** - Handler 层规范、测试规范、类型别名
- **[TEMPLATES.md](TEMPLATES.md)** - 完整代码模板
