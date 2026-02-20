# Commit 消息模板

本文档提供 Conventional Commits 规范的详细模板和示例。

---

## 消息格式

### 完整格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 最小格式

```
<type>: <subject>
```

### 带 Scope 格式

```
<type>(<scope>): <subject>
```

---

## Type 类型详解

### feat - 新功能

**使用场景**: 添加新的功能、接口、组件

```
feat(auth): 添加用户登录接口

- 实现 JWT token 生成
- 添加密码加密验证
- 支持多端登录限制
```

```
feat(axis-studio): 新增用户设置页面

实现用户个人设置功能，支持:
- 头像上传
- 昵称修改
- 密码修改
```

### fix - Bug 修复

**使用场景**: 修复 bug、错误、异常

```
fix(hexonal-app): 修复任务状态更新失败

问题: 并发更新时状态不一致
原因: 缺少乐观锁控制
方案: 添加版本号字段校验
```

```
fix(axis-studio): 修复登录页面样式问题

修复移动端登录按钮无法点击的问题
```

### docs - 文档更新

**使用场景**: 更新文档、注释、README

```
docs: 更新 API 接口文档

- 补充请求参数说明
- 添加响应示例
- 更新错误码列表
```

```
docs(readme): 更新项目启动说明

添加本地开发环境配置步骤
```

### style - 代码格式

**使用场景**: 格式化、缩进、空格（不影响逻辑）

```
style: 格式化代码

- 统一缩进为 4 空格
- 移除多余空行
- 调整 import 顺序
```

### refactor - 重构

**使用场景**: 重构代码，不改变功能行为

```
refactor(service): 重构任务查询逻辑

- 提取公共查询条件构建
- 使用策略模式处理不同状态
- 减少重复代码
```

### perf - 性能优化

**使用场景**: 性能优化、缓存、索引

```
perf(query): 优化任务列表查询

- 添加复合索引 (user_id, status, create_time)
- 使用 Redis 缓存热点数据
- 查询时间从 2s 降到 50ms
```

### test - 测试

**使用场景**: 添加、修改测试用例

```
test(service): 添加 TaskService 单元测试

覆盖以下场景:
- 创建任务
- 更新状态
- 删除任务
- 异常处理
```

### chore - 构建/工具

**使用场景**: 构建配置、依赖更新、工具调整

```
chore(deps): 更新 Spring Boot 版本

Spring Boot 3.2.x -> 3.3.x
同步更新相关依赖
```

```
chore(ci): 更新 Jenkinsfile 配置

- 使用 Docker Agent
- 添加构建缓存
- 优化部署流程
```

---

## Scope 范围建议

### 按模块划分

| Scope | 说明 | 示例 |
|-------|------|------|
| `hexonal-app` | Java 后端应用 | `feat(hexonal-app): 新增导出接口` |
| `axis-studio` | Next.js 前端应用 | `fix(axis-studio): 修复样式问题` |
| `api` | API 层 | `feat(api): 新增导出接口` |
| `service` | 服务层 | `refactor(service): 重构业务逻辑` |
| `dao` | 数据访问层 | `fix(dao): 修复分页查询` |
| `components` | 前端组件 | `feat(components): 添加新按钮组件` |

### 按功能划分

| Scope | 说明 | 示例 |
|-------|------|------|
| `auth` | 认证授权 | `feat(auth): 添加 OAuth2 支持` |
| `user` | 用户管理 | `feat(user): 添加用户导入` |
| `payment` | 支付功能 | `fix(payment): 修复支付回调` |
| `im` | 即时通讯 | `feat(im): 添加群聊功能` |

---

## 实际示例

### Java 服务变更

```
feat(hexonal-app): 添加任务批量操作接口

新增以下接口:
- POST /api/task/batch/create - 批量创建
- PUT /api/task/batch/status - 批量更新状态
- DELETE /api/task/batch - 批量删除

使用 @Transactional 保证事务一致性
添加参数校验和错误处理
```

### 前端项目变更

```
feat(axis-studio): 添加任务管理页面

- 任务列表展示 (分页、搜索、筛选)
- 任务详情弹窗
- 状态变更操作
- 使用 Radix UI 组件库
```

### 文档变更

```
docs(readme): 更新开发环境配置说明

- 补充 JDK 21 安装步骤
- 添加 Maven 镜像配置
- 更新启动命令示例
- 添加常见问题 FAQ
```

### 依赖更新

```
chore(deps): 升级 MyBatis-Plus 版本

MyBatis-Plus 3.5.5 -> 3.5.7

变更:
- 修复已知安全漏洞
- 支持新的分页特性
- 兼容 Spring Boot 3.x
```

---

## 不推荐的写法

### ❌ 避免的写法

```
# 太模糊
fix: 修复bug
update: 更新代码
change: 改了一些东西

# 缺少 type
修复任务状态更新问题

# type 使用错误
feat: 格式化代码  (应该用 style)
fix: 添加新功能   (应该用 feat)

# 全英文但中英混用
feat(task): add 任务接口
```

### ✅ 推荐的写法

```
# 清晰明确
fix(hexonal-app): 修复任务状态并发更新失败问题
feat(axis-studio): 添加用户认证页面
docs(api): 补充任务接口参数说明

# 纯中文或纯英文
feat(task): 添加任务优先级功能
feat(task): add task priority feature
```
