# GitHub 发布指南

本指南将帮助你把 ZenCore 项目发布到 GitHub 上。

---

## 📋 发布前检查清单

- [ ] Git 已安装 (`git --version`)
- [ ] GitHub 账号已注册
- [ ] 本地项目已初始化 Git
- [ ] SSH Key 已配置（推荐）或 HTTPS 已配置

---

## 🚀 第一步：创建 GitHub 仓库

### 方法一：网页创建（推荐新手）

1. 访问 [GitHub](https://github.com)
2. 点击右上角 **+** → **New repository**
3. 填写信息：
   - **Repository name**: `zencore`
   - **Description**: `ZenCore - 一切皆为插件的AI智能体框架`
   - **Public** 或 **Private**：选择 Public（开源）或 Private
   - **不要勾选** "Add a README file"（我们已经有了）
   - **不要勾选** "Add .gitignore"（我们已经有了）
4. 点击 **Create repository**
5. **复制仓库地址**（下一步用到）

### 方法二：GitHub CLI 创建

```bash
# 安装 GitHub CLI
# Windows: winget install GitHub.cli
# macOS: brew install gh
# Linux: sudo apt install gh

# 登录
gh auth login

# 创建仓库
gh repo create zencore --public --description "ZenCore - 一切皆为插件的AI智能体框架"
```

---

## 🔗 第二步：连接本地与远程仓库

### 如果是网页创建的仓库：

```bash
cd /CODE/zencore

# 添加远程仓库（替换 YOUR_USERNAME 为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/zencore.git

# 或者使用 SSH（推荐）
git remote add origin git@github.com:YOUR_USERNAME/zencore.git
```

### 验证远程仓库：

```bash
git remote -v
```

应该看到：
```
origin  https://github.com/YOUR_USERNAME/zencore.git (fetch)
origin  https://github.com/YOUR_USERNAME/zencore.git (push)
```

---

## 📤 第三步：提交代码并推送

### 1. 添加所有文件到暂存区：

```bash
git add .
```

### 2. 查看暂存状态：

```bash
git status
```

### 3. 创建提交：

```bash
git commit -m "✨ ZenCore v1.0 - 一切皆为插件的AI智能体框架

- 实现插件化架构
- 支持多外壳驱动
- 内置插件自动注册系统
- 禅 · 空 · 无限可能"
```

### 4. 推送到 GitHub：

```bash
# 首次推送（-u 设置上游分支）
git push -u origin main
```

> **注意**：如果报错 `refusing to merge unrelated histories`，使用：
> ```bash
> git pull origin main --allow-unrelated-histories
> ```

---

## 🏷️ 第四步：发布版本（可选）

### 创建版本标签：

```bash
# 添加版本标签
git tag -a v1.0.0 -m "ZenCore v1.0.0 正式版"

# 推送标签
git push origin v1.0.0
```

### 在 GitHub 网页创建 Release：

1. 进入仓库页面
2. 点击 **Releases** → **Draft a new release**
3. 填写：
   - **Tag version**: `v1.0.0`
   - **Release title**: `ZenCore v1.0.0`
   - **Description**: 发布说明
4. 点击 **Publish release**

---

## ⚙️ 第五步：配置仓库（可选）

### 添加主题描述：

1. 进入仓库 **Settings** → **Options**
2. 在 **Description** 填入：
   ```
   ZenCore - 一切皆为插件的AI智能体框架 | 空即是核，核即是一切
   ```
3. 在 **Website** 填入你的文档地址（如果有）

### 开启 Pages（可选）：

1. **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: main, / (root)
4. 点击 **Save**

### 添加徽章（Badges）：

在 `README.md` 顶部添加徽章：

```markdown
[![ZenCore](https://img.shields.io/badge/ZenCore-v1.0.0-FFD700?style=flat-square&logo=python)](https://github.com/YOUR_USERNAME/zencore)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg?style=flat-square)](https://www.python.org/)
```

---

## 🔄 更新代码到 GitHub

以后更新代码，只需：

```bash
# 1. 添加修改
git add .

# 2. 提交
git commit -m "你的提交信息"

# 3. 推送
git push
```

---

## 🆘 常见问题

### Q: 推送被拒绝？

```bash
# 原因：远程仓库有本地没有的提交
# 解决：先拉取再推送
git pull origin main --rebase
git push origin main
```

### Q: SSH 连接失败？

```bash
# 检查 SSH Key
cat ~/.ssh/id_rsa.pub

# 如果没有，生成新的
ssh-keygen -t rsa -C "your_email@example.com"

# 把公钥复制到 GitHub Settings -> SSH Keys
```

### Q: 如何撤销上一次的提交？

```bash
# 撤销提交，但保留修改
git reset --soft HEAD~1

# 撤销提交，且不保留修改
git reset --hard HEAD~1
```

---

## 📚 相关资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 官方文档](https://docs.github.com/)
- [ZenCore 使用指南](./使用指南.md)
- [插件编写指南](./plugins/插件编写指南.md)
- [外壳驱动指南](./drivers/驱动指南.md)

---

**祝你发布成功！🎉**
