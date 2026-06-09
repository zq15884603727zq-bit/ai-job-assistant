# AI 求职助手（Dify 平台）

基于 Dify 平台构建的 AI 求职助手，提供 JD 解析、简历匹配、面试准备等智能化求职辅助功能。

## 项目结构

```
ai-job-assistant/
├── data/                   # 数据文件
│   ├── raw/                # 原始 JD 数据（HTML/PDF/文本）
│   └── knowledge_base/     # 处理后的知识库文件（Markdown/JSONL）
├── prompts/                # Dify Prompt 模板
│   ├── jd_parser/          # JD 解析相关 Prompt
│   ├── resume_matcher/     # 简历匹配相关 Prompt
│   └── interview_coach/    # 面试辅导相关 Prompt
├── scripts/                # 数据处理与测试脚本
│   ├── data_processing/    # 数据清洗、格式转换脚本
│   └── dify_test/          # Dify API 测试脚本
├── tests/                  # 测试用例与结果
│   ├── test_cases/         # 测试用例
│   └── test_results/       # 测试结果记录
└── README.md               # 项目说明
```

## 功能模块

| 模块 | 说明 | Dify 应用类型 |
|------|------|--------------|
| JD 解析器 | 从职位描述中提取关键信息（技能、经验、薪资等） | Chatflow / Workflow |
| 简历匹配器 | 将简历与 JD 进行智能匹配，输出匹配度与改进建议 | Workflow |
| 面试教练 | 基于 JD 生成面试问题与模拟面试 | Agent / Chatbot |

## 快速开始

1. 将原始 JD 数据放入 `data/raw/`
2. 运行数据预处理脚本：`python scripts/data_processing/preprocess.py`
3. 将生成的 Knowledge Base 文件导入 Dify 知识库
4. 将 `prompts/` 中的模板配置到对应的 Dify 应用中

## 环境要求

- Python 3.10+
- Dify 平台账号
- 依赖见各脚本目录下的 `requirements.txt`
