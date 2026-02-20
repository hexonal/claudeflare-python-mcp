---
name: git-workflow
description: |
  Git 工作流自动化 - 构建检查、代码提交、推送。

  ⚠️ 重要约束：
  - 本项目默认禁止所有 Git 版本控制操作（git commit/push/merge/rebase 等）
  - 这是为了防止误操作、确保质量门禁、统一工作流
  - 只有当用户明确说出触发词时，才会激活本 skill 并解除限制

  触发词：
  当用户说"提交代码"、"推送到远程"、"合并分支"、"同步到主分支"、
  "git commit"、"git push"、"完成开发提交"、"提交并推送"时自动激活。

  激活后行为：
  1. 执行构建检查（必须通过）
  2. 生成 Conventional Commit 消息
  3. git add → commit → push
  4. 限制自动恢复

  关键词：git, commit, push, merge, 提交, 推送, 合并, 工作流, 同步代码
---

# Git 工作流 Skill

本 Skill 实现 infras-hexonal 仓库的自动化 Git 工作流：**构建检查 → 提交 → 推送**。

---

## 🔓 权限声明

> **本 Skill 覆盖 CLAUDE.md 中的 Git 操作限制**

当 `git-workflow` skill 被激活时，**允许执行**以下操作：

| 命令 | 用途 |
|------|------|
| `git add` | 暂存变更文件 |
| `git commit` | 提交变更 |
| `git push` | 推送到远程 |
| `git merge` | 合并分支 |
| `git checkout` | 切换分支 |

**前提条件**：必须通过构建检查（构建成功 exit code = 0）。

---

## 🔴 核心工作流

### 完整流程

```
1. 检测项目类型 (Java/Go/TypeScript)
       ↓
2. 执行构建检查
       ↓ (成功)
3. 生成 Conventional Commit 消息
       ↓
4. git add → commit → push
       ↓
5. 报告完成状态
```

### 安全检查清单（构建前验证）

执行 Git 操作前**必须**通过以下检查：

- [ ] 构建命令执行成功（exit code = 0）
- [ ] 当前分支**不是** main/master
- [ ] 有实际的代码变更（`git status` 非空）

---

## 🟡 构建命令映射

| 项目类型 | 检测文件 | 构建命令 |
|---------|---------|---------|
| Java | `pom.xml` | `mvn clean package -DskipTests` |
| Go | `go.mod` | `go build ./...` |
| TypeScript (pnpm) | `pnpm-lock.yaml` | `pnpm build` |
| TypeScript (npm) | `package-lock.json` | `npm run build` |

**检测优先级**: pom.xml > go.mod > pnpm-lock.yaml > package.json

---

## 🟢 Conventional Commits 快速参考

### 格式

```
<type>(<scope>): <subject>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): 添加登录接口` |
| `fix` | Bug 修复 | `fix(task): 修复任务状态更新` |
| `docs` | 文档更新 | `docs: 更新 README` |
| `style` | 代码格式 | `style: 格式化代码` |
| `refactor` | 重构 | `refactor(service): 重构任务服务` |
| `perf` | 性能优化 | `perf(query): 优化查询性能` |
| `test` | 测试 | `test(api): 添加单元测试` |
| `chore` | 构建/工具 | `chore(deps): 更新依赖版本` |

### 自动判断规则

| 变更类型 | 推荐 Type |
|---------|----------|
| 新文件 + 功能代码 | `feat:` |
| 修改现有代码 + 修复相关 | `fix:` |
| 只改 .md 文件 | `docs:` |
| 只改格式/空格 | `style:` |
| 改 pom.xml/package.json | `chore:` |

---

## 🔧 使用方式

直接用自然语言触发（语义激活）：

| 触发语句 | 执行内容 |
|---------|---------|
| "提交代码" / "提交并推送" | 完整工作流：构建 → 提交 → 推送 |
| "推送到远程" / "只推送" | 仅推送 |
| "完成开发，同步代码" | 完整工作流 |

> **注意**: 本 Skill 通过 `description` 语义匹配自动激活，不支持 `/command` 形式触发

---

## ⚠️ 错误处理

| 错误类型 | 处理策略 |
|---------|---------|
| 构建失败 | **阻止提交**，显示错误信息，要求修复 |
| 合并冲突 | 提示用户手动解决，给出冲突文件列表 |
| Push 失败 | 检查网络，提示重试或手动操作 |

---

## 📚 更多信息

详细参考：[@REFERENCE.md](./REFERENCE.md)
Commit 模板：[@TEMPLATES.md](./TEMPLATES.md)
