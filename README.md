# Exam Practice

随机抽题练习工具，支持选择题、判断题、填空题。

## 快速开始

```bash
# 安装依赖
uv sync

# 启动服务
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000
```

浏览器打开 `http://127.0.0.1:8000`。

## 题型

| 题型 | 说明 |
| --- | --- |
| 选择题 (multiple-choice) | 单选 / 多选，选项随机打乱 |
| 判断题 (judgement) | 选择 正确 或 错误 |
| 填空题 (cloze) | 文本输入，大小写不敏感 |

## 添加题目

在 `data/` 目录下创建 `.json` 文件，格式如下：

```json
[
    { "type": "multiple-choice", "stem": "题干", "choice": ["选项A", "选项B"], "answer": ["选项A"] },
    { "type": "judgement",      "stem": "题干", "answer": "TRUE" },
    { "type": "cloze",          "stem": "题干___", "answer": ["答案"] }
]
```

判断题的 `answer` 可以是字符串 `"TRUE"` / `"FALSE"`，其他类型的 `answer` 均为数组。

## 掌握追踪

答对同一道题 **3 次** 后视为已掌握，后续抽题会自动跳过已掌握的题目。进度保存在浏览器 localStorage 中。
