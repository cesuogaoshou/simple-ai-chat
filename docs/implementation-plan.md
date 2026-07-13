# Simple AI Chat Implementation Plan

## Goal

实现一个可本地运行的最小 AI Chat 项目，支持通过环境变量切换 DeepSeek 和 OpenAI。

## Steps

1. 初始化工程：
   - 创建 Git 仓库并使用 `main` 分支。
   - 创建 `.gitignore`，忽略 `.env`、虚拟环境和缓存文件。
   - 创建 `requirements.txt` 和 `.env.example`。

2. 实现 Provider 配置：
   - 新建 `ai_chat/config.py`。
   - 定义 `ProviderConfig`。
   - 实现 `load_provider_config()`。
   - 用单元测试覆盖默认 DeepSeek、OpenAI、未知 Provider、缺少 API Key。

3. 实现聊天调用：
   - 新建 `ai_chat/chat.py`。
   - 定义统一 system prompt。
   - 实现 `build_chat_messages()`。
   - 实现 `create_chat_client()`。
   - 实现 `request_chat_completion()`。

4. 实现 Streamlit UI：
   - 新建 `app.py`。
   - 加载 `.env`。
   - 展示配置状态、聊天历史、输入框。
   - 支持清空对话。
   - 捕获配置错误和 API 请求错误。

5. 补齐文档：
   - README 写清安装、配置、运行、验证和 GitHub 远端。
   - `docs/design.md` 写清架构、数据流、范围边界。

6. 验证和提交：
   - 运行 `pytest`。
   - 运行 `compileall`。
   - 配置 GitHub 远端 `https://github.com/cesuogaoshou/simple-ai-chat.git`。
   - 首次提交并推送 `main`。

## Acceptance Criteria

- `pytest` 全部通过。
- `compileall` 能编译 `app.py` 和 `ai_chat`。
- 缺少 API Key 时页面给出明确配置提示。
- `AI_PROVIDER=deepseek` 时读取 DeepSeek 配置。
- `AI_PROVIDER=openai` 时读取 OpenAI 配置。
- 有效 API Key 下可以发送消息并显示助手回复。
- `.env` 不会进入 Git 提交。
