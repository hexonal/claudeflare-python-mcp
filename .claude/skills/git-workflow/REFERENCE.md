# Git 工作流详细参考

本文档提供 `git-workflow` Skill 的完整实现细节和技术参考。

---

## 完整工作流详解

### Step 1: 检测项目类型

```bash
# 检测逻辑（按优先级）
if [ -f "pom.xml" ]; then
    PROJECT_TYPE="java"
elif [ -f "go.mod" ]; then
    PROJECT_TYPE="go"
elif [ -f "pnpm-lock.yaml" ]; then
    PROJECT_TYPE="typescript-pnpm"
elif [ -f "package.json" ]; then
    PROJECT_TYPE="typescript"
else
    PROJECT_TYPE="unknown"
fi
```

**多项目场景处理**：
- 如果当前目录有多个项目标识文件，按 `pom.xml > go.mod > pnpm-lock.yaml > package.json` 优先级处理
- 建议在具体项目子目录执行，而非仓库根目录

### Step 2: 执行构建检查

| 项目类型 | 构建命令 | 超时时间 | 成功标准 |
|---------|---------|---------|---------|
| Java | `mvn clean package -DskipTests` | 5 分钟 | exit code = 0 |
| Go | `go build ./...` | 2 分钟 | exit code = 0 |
| TypeScript (pnpm) | `pnpm build` | 3 分钟 | exit code = 0 |
| TypeScript (npm) | `npm run build` | 3 分钟 | exit code = 0 |

**构建失败处理**：
```
❌ 构建失败，停止提交流程

错误信息:
[显示构建错误输出]

请修复以上问题后重新说"提交代码"
```

### Step 3: 生成 Commit 消息

#### 自动分析变更内容

```bash
# 获取变更文件列表
git status --porcelain

# 分析变更类型
NEW_FILES=$(git status --porcelain | grep "^A" | wc -l)
MODIFIED_FILES=$(git status --porcelain | grep "^M" | wc -l)
DELETED_FILES=$(git status --porcelain | grep "^D" | wc -l)
```

#### 智能 Type 推断

| 条件 | 推断 Type |
|------|----------|
| 新增 .java/.go/.ts/.tsx 文件 | `feat` |
| 仅修改现有代码 | `fix` 或 `refactor` |
| 仅 .md 文件变更 | `docs` |
| 仅 pom.xml/package.json/go.mod | `chore` |
| 仅格式调整（无逻辑变更） | `style` |
| 新增/修改测试文件 | `test` |

#### Scope 推断

根据变更文件路径自动推断 scope：
- `hexonal-app/*` → `hexonal-app`
- `axis-studio/*` → `axis-studio`
- `*/api/*` → `api`
- `*/dao/*` → `dao`
- `*/service/*` → `service`
- `*/components/*` → `components`

### Step 4: 执行 Git 操作

```bash
# 1. 暂存所有变更
git add .

# 2. 提交（使用 HEREDOC 确保格式正确）
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

<body>

Generated with AI

Co-Authored-By: <git-user>
EOF
)"

# 3. 推送到当前分支
git push origin <current_branch>
```

---

## 错误处理详解

### 构建失败

**症状**: `mvn clean package` / `go build` / `pnpm build` 返回非零退出码

**处理**:
1. 显示完整错误输出
2. **阻止后续 Git 操作**
3. 提示用户修复问题

```
❌ 构建检查失败

项目类型: Java
构建命令: mvn clean package -DskipTests
退出码: 1

错误输出:
[COMPILER] xxx.java:[10,5] 找不到符号
...

📋 下一步: 请修复编译错误后重新说"提交代码"
```

### Push 失败

**症状**: `git push` 失败（网络问题或权限问题）

**处理**:
```
❌ 推送失败

错误: fatal: unable to access 'https://...': Could not resolve host

📋 可能原因:
1. 网络连接问题
2. 远程仓库地址错误
3. 认证凭据过期

📋 建议操作:
1. 检查网络连接
2. 运行 git remote -v 确认远程地址
3. 手动执行 git push origin <branch>
```

---

## 项目特定配置

不同项目可以在各自的 CLAUDE.md 中覆盖默认构建命令：

### Java 项目覆盖

```markdown
## Git 工作流配置

| 配置项 | 值 |
|-------|---|
| 构建命令 | `mvn clean package -pl <module> -am -DskipTests` |
```

### TypeScript 项目覆盖

```markdown
## Git 工作流配置

| 配置项 | 值 |
|-------|---|
| 构建命令 | `pnpm type-check && pnpm build` |
```

---

## 执行报告模板

成功完成后的报告格式：

```
✅ Git 工作流完成

📋 执行摘要:
├─ 项目类型: Java
├─ 构建检查: ✅ 通过
├─ 提交: feat(hexonal-app): 添加用户认证接口
└─ 推送: ✅ origin/feature/auth

📊 变更统计:
├─ 新增文件: 3
├─ 修改文件: 2
└─ 删除文件: 0

🔗 相关链接:
└─ 当前分支: feature/auth
```
