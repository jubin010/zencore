# plugin_builder

## 描述
插件构建器 — 让 AI 能自我编写插件

## 工具
| 工具 | 参数 | 描述 |
|------|------|------|
| write_plugin | plugin_name, code, plugin_md | 编写新插件 |
| load_plugin | plugin_name | 加载指定插件 |
| unload_plugin | plugin_name | 卸载指定插件 |
| reload_plugins | 无 | 重新加载所有插件 |
| list_plugins | 无 | 列出所有已加载的插件 |
| get_plugin_template | plugin_name | 获取插件开发模板 |
| get_plugin_info | plugin_name | 读取插件的 plugin.md 详情 |
| get_plugin_readme | 无 | 读取插件编写指南 |
| get_available_tools | 无 | 获取所有可用工具列表 |
| validate_code | code | 验证代码语法 |
| delete_plugin | plugin_name | 删除插件目录 |
