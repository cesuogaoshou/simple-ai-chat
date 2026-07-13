# Simple AI Chat

一个最小可用的 AI 聊天项目。界面使用 Streamlit，模型调用使用 OpenAI Python SDK 的 OpenAI-compatible Chat Completions API。默认接入 DeepSeek，也可以通过环境变量切换到 OpenAI。

## 你会得到什么

- 一个本地可运行的 Web 聊天界面
- 会话内上下文记忆
- DeepSeek / OpenAI 可配置切换
- `.env` 管理 API Key、Base URL 和模型名
- 基础错误提示，避免把密钥输出到页面或日志
- 单元测试覆盖 Provider 配置和消息构造逻辑

## 快速启动

在 Windows PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，填入你要使用的 Provider 的 API Key。

启动应用：

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

启动后浏览器会打开本地 Streamlit 页面。如果没有自动打开，可以访问终端中显示的 Local URL，通常是：

```text
http://localhost:8501
```

## 配置 DeepSeek

项目默认使用 DeepSeek：

```env
AI_PROVIDER=deepseek

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

DeepSeek 兼容 OpenAI Chat Completions API 格式，但需要使用 DeepSeek 自己的 API Key、Base URL 和模型名。

## 配置 OpenAI

把 `.env` 改成：

```env
AI_PROVIDER=openai

OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.6
```

## 环境变量说明

| 变量 | 说明 |
| --- | --- |
| `AI_PROVIDER` | 当前模型服务商，只支持 `deepseek` 或 `openai` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | DeepSeek API Base URL，默认 `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek 模型名，默认 `deepseek-v4-pro` |
| `OPENAI_API_KEY` | OpenAI API Key |
| `OPENAI_BASE_URL` | OpenAI API Base URL，默认 `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI 模型名，默认 `gpt-5.6` |

## 项目结构

```text
.
├── ai_chat/
│   ├── chat.py              # Chat Completions 消息构造和模型请求
│   └── config.py            # Provider 配置解析
├── docs/
│   ├── design.md            # 设计说明
│   └── implementation-plan.md
├── tests/
│   ├── test_chat.py
│   └── test_config.py
├── .env.example             # 环境变量模板
├── .gitignore
├── app.py                   # Streamlit 应用入口
├── README.md
└── requirements.txt
```

## 运行测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

## 常见问题

### 页面提示缺少 API Key

确认已经复制 `.env.example` 为 `.env`，并填写了当前 Provider 对应的 key。

例如 `AI_PROVIDER=deepseek` 时，需要填写：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 想切换 Provider

修改 `.env` 中的 `AI_PROVIDER`，然后重启 Streamlit。

```env
AI_PROVIDER=openai
```

或：

```env
AI_PROVIDER=deepseek
```

### 请求模型失败

优先检查这几项：

- API Key 是否有效
- 模型名是否存在
- Base URL 是否正确
- 当前网络是否能访问对应服务商

## GitHub 仓库

```text
https://github.com/cesuogaoshou/simple-ai-chat
```
