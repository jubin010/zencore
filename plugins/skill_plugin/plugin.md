# skill_plugin

## 描述
技能管理 — 按需装备的专业能力

## 工具

| 工具 | 参数 | 描述 |
|------|------|------|
| list_skills | 无 | 列出所有可用技能（渐进式：标题 + 2行描述） |
| get_skill_info | skill_name | 查看技能完整描述 |
| create_skill | skill_name, skill_md | 创建新技能 |
| equip_skill | skill_name | 装备技能 |

## 技能文件结构

```
plugins/skills/<skill_name>/
└── skill.md       # 技能描述
```

## skill.md 渐进式披露规则

技能描述采用渐进式披露，列表只显示摘要：

- **第1行**：标题（`# 标题`），列表中显示
- **第2行**：简短描述，列表中显示（最多2行）
- **后续内容**：详细说明，仅 `get_skill_info` 时展示

示例：
```markdown
# 开发者

专注于代码开发、调试、重构的专业技能。

## 职责
- 编写和维护代码
- 调试和修复问题
...
```

## 创建技能

```
create_skill(
    skill_name="xxx",      # 技能名（英文，无空格）
    skill_md="xxx"         # 技能描述（Markdown 格式）
)
```