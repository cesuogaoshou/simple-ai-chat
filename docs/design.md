# Simple AI Chat Design

## Goal

构建一个最简单的 AI Chat 项目：本地一条命令启动，浏览器中输入消息，后端调用可配置的大模型 Provider 返回回复。

## Scope

v1 只包含聊天闭环和工程基础设施：

- Streamlit 单页 UI
- 会话内历史
- DeepSeek/OpenAI Provider 配置
- OpenAI-compatible Chat Completions 调用
- README、设计文档、实现计划、Git 初始化

v1 不包含登录、数据库、RAG、文件上传、长期记忆、工具调用、部署流水线。

## Architecture

项目拆成三个小边界：

- `app.py`：Streamlit UI、用户输入、页面状态和错误展示。
- `ai_chat/config.py`：读取环境变量并生成统一的 `ProviderConfig`。
- `ai_chat/chat.py`：构造 Chat Completions messages，创建 SDK client，发起模型请求。

这种拆法让 Provider 配置和消息格式可以用单元测试覆盖，Streamlit 层保持薄。

## Provider Configuration

`AI_PROVIDER` 只接受 `deepseek` 或 `openai`。

- `deepseek` 读取 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`。
- `openai` 读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。

默认 Provider 是 `deepseek`，默认 Base URL 和模型名来自 `.env.example`。API Key 永远不写入仓库，只通过 `.env` 本地配置。

## Data Flow

1. Streamlit 启动时加载 `.env`。
2. `load_provider_config()` 解析当前 Provider。
3. 用户发送消息后，消息保存到 `st.session_state.messages`。
4. `build_chat_messages()` 添加 system prompt，并附加当前会话历史。
5. `client.chat.completions.create()` 请求模型。
6. 回复展示在页面中，并保存回会话历史。

## Error Handling

- Provider 名称错误：页面提示只支持 `deepseek` 和 `openai`。
- 当前 Provider 的 API Key 缺失：页面提示复制 `.env.example` 并填写 key。
- 模型请求异常：页面显示简短错误类型和排查方向，不打印 API Key。

## Testing Strategy

单元测试覆盖可稳定验证的纯逻辑：

- 默认加载 DeepSeek 配置。
- 显式选择 OpenAI 配置。
- 拒绝未知 Provider。
- 缺少 API Key 时报错。
- Chat Completions messages 包含 system prompt。
- 忽略未知 role 的历史消息。

Streamlit UI 和真实模型请求通过手动验收验证。
