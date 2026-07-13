# Simple AI Chat

一个最小可用的 AI Chat 项目，使用 Streamlit 提供聊天界面，使用 OpenAI Python SDK 调用 OpenAI-compatible Chat Completions API。默认 Provider 是 DeepSeek，也可以通过环境变量切换到 OpenAI。

## 功能

- 单页聊天界面
- 会话内聊天历史
- 支持 `deepseek` 和 `openai` 两种 Provider
- 使用 `.env` 管理 API Key、Base URL 和模型名
- 配置错误和 API 请求错误会在页面中提示

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，至少填入当前 Provider 对应的 API Key。

启动应用：

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## 配置 DeepSeek

`.env.example` 默认使用 DeepSeek：

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

DeepSeek 兼容 OpenAI Chat Completions API 格式，但需要使用 DeepSeek 的 API Key、Base URL 和模型名。

## 配置 OpenAI

切换到 OpenAI：

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.6
```

## 项目结构

```text
.
├── ai_chat/
│   ├── chat.py
│   └── config.py
├── docs/
│   ├── design.md
│   └── implementation-plan.md
├── tests/
│   ├── test_chat.py
│   └── test_config.py
├── .env.example
├── .gitignore
├── app.py
├── README.md
└── requirements.txt
```

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

## GitHub

计划连接的远端仓库：

```text
https://github.com/cesuogaoshou/simple-ai-chat
```

首次推送命令：

```powershell
git remote add origin https://github.com/cesuogaoshou/simple-ai-chat.git
git push -u origin main
```
