# Git 工作流规则

## ⚠️ 重要约束

### 默认禁止 Git 版本控制操作

**本项目严格限制 Git 操作，防止意外提交或推送。**

所有改变仓库状态的 Git 命令**默认禁止**，包括但不限于：
- `git commit`
- `git push`
- `git merge`
- `git rebase`
- `git reset --hard`
- `git cherry-pick`

### 为什么设置限制

1. **防止误操作**：避免在未经检查的情况下提交代码
2. **确保质量门禁**：所有提交前必须通过构建验证
3. **统一工作流**：强制使用标准化的提交流程
4. **可追溯性**：所有提交都有明确的触发记录

---

## 如何解除限制（唯一方式）

### 触发条件

用户必须**明确说出**以下触发词之一：

| 触发词 | 说明 |
|--------|------|
| "提交代码" | 完整工作流：构建 → 提交 → 推送 |
| "推送到远程" | 仅推送（跳过合并） |
| "合并分支" | 仅合并到目标分支 |
| "同步到主分支" | 同"合并分支" |
| "git commit"（作为明确指令） | 理解为"提交代码" |
| "git push"（作为明确指令） | 理解为"推送到远程" |

### 激活后的行为

触发词说出后，自动激活 `git-workflow` skill，执行以下流程：

```
1. 构建检查（必须通过）
   ├─ Java: mvn clean package -DskipTests
   ├─ Go: go build ./...
   └─ TypeScript: pnpm build 或 npm run build

2. 生成 Conventional Commit 消息
   └─ 格式：<type>(<scope>): <subject>

3. Git 操作
   ├─ git add .
   ├─ git commit -m "..."
   └─ git push

4. 限制自动恢复
   └─ 工作流完成后，Git 操作再次被限制
```

---

## Commit 格式

遵循 Conventional Commits 规范：

```
<type>(<scope>): <subject>

Types:
- feat: 新功能
- fix: 修复 Bug
- docs: 文档更新
- style: 代码格式（不影响功能）
- refactor: 重构
- perf: 性能优化
- test: 测试相关
- chore: 构建/工具链
```

**示例**：
```
feat(hexonal-app): 添加用户认证接口
fix(axis-studio): 修复登录页面样式问题
docs(readme): 更新项目架构说明
```

---

## 安全检查

在执行 Git 操作前，`git-workflow` skill 会自动执行以下检查：

| 检查项 | 说明 | 失败处理 |
|--------|------|---------|
| 构建成功 | exit code = 0 | ❌ 阻止提交 |
| 不在 main/master | 当前分支不是主分支 | ⚠️ 警告但继续 |
| 无未跟踪的敏感文件 | .env、credentials.json 等 | ⚠️ 警告并排除 |

---

## 违规处理

### 场景 1：Claude 尝试直接执行 Git 命令

```
用户："修改了代码"
Claude：[内部检测到需要提交]
        ❌ 错误：Git 操作被限制
        💡 解决：请明确说"提交代码"以激活 git-workflow
```

### 场景 2：用户未说触发词但期望提交

```
用户："好了，完成了"
Claude："修改已完成。如需提交代码，请说'提交代码'。"
```

### 场景 3：构建失败时的处理

```
用户："提交代码"
Claude：[激活 git-workflow]
        执行构建检查...
        ❌ 构建失败：3 个编译错误
        🔧 请修复错误后重新说"提交代码"
```

---

## 详细规范

完整 Git 工作流规范见：[.claude/skills/git-workflow/SKILL.md](../skills/git-workflow/SKILL.md)

**相关配置**：
- Commit 模板：[git-workflow/TEMPLATES.md](../skills/git-workflow/TEMPLATES.md)
- 工作流详细步骤：[git-workflow/REFERENCE.md](../skills/git-workflow/REFERENCE.md)
