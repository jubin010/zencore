# AgentCore 插件注册表

> **智能体的自我认知档案** - 告诉AI自己有什么能力、如何使用

## 📋 插件列表

| 插件 | 描述 | 工具数 |
|------|------|--------|
| `plugin_builder` |  plugin_builder.py - 插件构建器 功能：让 AI 和人类都能... | 1 |
| `watcher_plugin` | 文件监听插件 - 自动更新插件注册表... | 2 |

## 🔧 工具注册表

| 工具 | 所属插件 | 描述 |
|------|----------|------|
| `scan_plugins` | watcher_plugin | 扫描插件目录 |
| `update_plugins_md` | watcher_plugin | 更新 plugins.md 注册表 |
| `动态加载` | plugin_builder | 此插件提供动态加载能力 |

## 📦 插件开发指南

### 人类开发
```bash
# 1. 创建插件文件
touch plugins/my_plugin.py

# 2. 编写插件代码（参考 插件编写指南.md）

# 3. 此插件会自动更新本注册表 ✓
```

### AI 自动进化
```
AI 发现需要某个工具 → 调用 write_plugin() → 自动更新本注册表 ✓
```

---

*最后更新: 2026-04-03 16:17:30*
