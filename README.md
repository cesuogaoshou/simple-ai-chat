# Simple AI Chat

Simple AI Chat 是一个本地优先的 AI 聊天应用。它提供一个可以直接在浏览器里使用的聊天界面，支持连接 DeepSeek 或 OpenAI 兼容接口，并围绕「多会话管理」「提示词预设」「本地备份」「会话整理」做了完整能力建设。

这个项目的目标不是做一个庞大的平台，而是做一个轻量、可运行、可维护、可继续迭代的个人 AI Chat 工具。

## 项目已经完成了什么

项目目前已经从最基础的单轮聊天，迭代到了一个具备本地会话库能力的 AI 聊天应用。

已经实现的主要成果包括：

- 搭建了 Streamlit Web 聊天界面，可以在本地浏览器中使用。
- 接入 OpenAI-compatible Chat Completions API，默认支持 DeepSeek，也支持切换到 OpenAI。
- 实现流式回复，让模型输出可以边生成边展示。
- 实现本地多会话管理，不同聊天可以独立保存、切换和整理。
- 实现本地 JSON 持久化，会话记录保存在 `.data/` 目录下。
- 支持自动会话标题，根据第一条用户消息生成新聊天标题。
- 支持会话置顶，让重要聊天保持在列表前面。
- 支持按标题和消息内容搜索历史聊天。
- 支持会话标签和备注，用于给聊天分类、补充背景说明。
- 支持按标签筛选会话。
- 支持对筛选结果批量添加或移除标签。
- 支持导出当前会话、全部会话和筛选结果。
- 支持从 JSON 导入会话，方便备份和迁移。
- 支持 Markdown 导出当前聊天，方便阅读和分享。
- 支持内置提示词预设和自定义提示词预设。
- 支持调整生成参数，如温度和最大输出长度。
- 支持删除最后一轮对话。
- 删除当前聊天前需要确认，降低误操作风险。
- 配置了基础测试、代码检查和 GitHub Actions CI。

## 功能亮点

### 本地优先

聊天记录、提示词预设和会话元数据都优先保存在本地。项目适合个人使用、原型验证、学习 AI Chat 应用结构，也适合作为后续扩展的基础版本。

### 多会话会话库

应用不只是一个单页聊天窗口，还提供了本地会话库。用户可以创建多个聊天，搜索历史内容，置顶重要会话，用标签和备注管理不同主题。

### 可整理、可备份

会话可以按标签筛选，也可以把筛选后的结果单独导出。这样既能完整备份全部聊天，也能只导出某一类项目、主题或工作流相关的会话。

### 提示词预设

应用内置了常见使用场景的提示词预设，也允许用户保存自己的自定义系统提示词。这样可以在翻译、代码解释、需求分析、写作润色等场景之间快速切换。

### 工程化基础

项目包含单元测试、编译检查、Ruff 代码检查和 GitHub Actions CI。核心逻辑被拆分到 `ai_chat/` 模块中，便于继续维护和迭代。

## 快速启动

在 Windows PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，填入你要使用的模型服务 API Key。

启动应用：

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

启动后通常会自动打开浏览器。如果没有自动打开，可以访问终端中显示的本地地址，通常是：

```text
http://localhost:8501
```

## 基本配置

默认使用 DeepSeek：

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
```

切换到 OpenAI：

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
```

也可以在 `.env` 中配置对应的 Base URL 和模型名称。

## 项目结构

```text
.
|-- ai_chat/                 # 聊天、配置、预设、会话等核心逻辑
|-- docs/                    # 设计文档、执行计划和版本演进记录
|-- tests/                   # 单元测试
|-- .streamlit/              # Streamlit 配置示例
|-- app.py                   # Streamlit 应用入口
|-- README.md
|-- CHANGELOG.md
|-- requirements.txt
`-- pyproject.toml
```

## 质量检查

本地可以运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

GitHub Actions 会在推送和 Pull Request 时执行同类检查。

## 后续可以怎么迭代

这个项目已经具备一个本地 AI Chat 工具的完整基础，后续可以继续沿几个方向增强：

- **聊天编辑体验**：支持编辑上一条用户消息、重新生成回复、复制回复。
- **提示词库增强**：支持导入/导出提示词预设、编辑已保存预设、给预设分类。
- **本地数据安全**：增加自动备份、导入前预览、删除撤销、本地加密选项。
- **Provider 配置管理**：支持保存多个常用模型配置，在不同服务和模型之间快速切换。
- **会话整理能力**：继续增强标签、筛选、批量操作和归档能力。
- **部署体验**：继续完善 Streamlit Cloud 或其他轻量部署方式的说明和配置。

## 适合用来做什么

- 作为个人本地 AI Chat 工具。
- 作为 Streamlit + OpenAI-compatible API 的学习项目。
- 作为多会话 AI 应用的基础模板。
- 作为后续扩展 RAG、文件上传、账号系统或云同步能力的起点。

## 仓库

```text
https://github.com/cesuogaoshou/simple-ai-chat
```
