---
name: publish-article
description: 文章发布助手。帮助用户将文章从素材目录（03_Assets）移动到已发布目录（04_Published），并更新 frontmatter 字段。需要用户提供发布链接和文章分类。使用场景：用户说"发布这篇文章"、"把文章移到已发布目录"、"这篇文章已经发布了"等。
---

# 文章发布助手

这个技能帮助你将已发布的文章从素材目录移动到已发布目录，并更新相关字段。

## 工作流程

1. **确认文件**：确认用户要发布的文章文件
2. **获取信息**：从用户获取发布链接和分类
3. **更新字段**：更新 frontmatter 字段
4. **移动文件**：将文件移动到 `04_Projects/AI_Media/04_Published/` 目录

## 字段更新规则

### 从 asset 到 published_article 的字段变化

| 字段 | 更新前 | 更新后 |
|------|--------|--------|
| type | asset | published_article |
| status | 待发布/草稿 | 已完成 |
| publish_date | 无 | 当前日期（YYYY-MM-DD） |
| category | 无 | 用户指定的分类 |
| published_url | 无 | URL（如：https://mp.weixin.qq.com/s/xxx） |
| tags | 进行中 | 已完成 |
| refs | 无/空 | 发布链接 |

### 分类选项

根据 `05_Templates/笔记字段速查表.md`，published_article 的 category 可选值：
- 技术教程
- 工具推荐
- 方法论
- 案例分析

## 执行步骤

### Step 1: 确认文件

用户会指定要发布的文件，例如：
- "发布这篇文章"（如果正在编辑某个文件）
- "发布 [文件名]"
- "把 [文件名] 移到已发布目录"

### Step 2: 获取必要信息

询问用户：
1. **发布链接**："请提供文章的发布链接"
2. **分类**："请选择文章分类：（1）技术教程 （2）工具推荐 （3）方法论 （4）案例分析"

### Step 3: 更新 frontmatter

按照字段更新规则更新文件的 frontmatter。

### Step 4: 移动文件

将文件从 `04_Projects/AI_Media/03_Assets/` 移动到 `04_Projects/AI_Media/04_Published/`

### Step 5: 提交更改

创建 git 提交：
```bash
git add -A
git commit -m "feat: 发布文章 [文章标题]

- 移动到已发布目录
- 更新 type: published_article
- 添加 publish_date 和 published_url"
git push origin main
```

## 示例

### 输入
```
用户：发布 网站Google搜不到？3步让搜索引擎收录你的内容.md
```

### 输出
```
助手：请提供文章的发布链接。
用户：https://mp.weixin.qq.com/s/vI3aq-ut3KFWb-I0LV5YuA
助手：请选择文章分类：（1）技术教程 （2）工具推荐 （3）方法论 （4）案例分析
用户：技术教程
助手：[执行更新和移动操作，提交 git]
```

## 注意事项

1. **文件路径**：确保文件在 `04_Projects/AI_Media/03_Assets/` 目录下
2. **备份**：移动前建议先提交当前更改
3. **日期格式**：publish_date 使用 YYYY-MM-DD 格式
4. **published_url 格式**：直接使用 URL，例如 `https://mp.weixin.qq.com/s/xxx`
5. **分类验证**：确保用户选择的分类在可选值范围内
