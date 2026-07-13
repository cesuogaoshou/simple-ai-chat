from ai_chat.chat import SYSTEM_PROMPT, build_chat_messages


def test_builds_chat_completion_messages_with_system_prompt():
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]

    messages = build_chat_messages(history)

    assert messages == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]


def test_ignores_messages_with_unknown_roles():
    history = [
        {"role": "tool", "content": "ignored"},
        {"role": "user", "content": "保留这条"},
    ]

    messages = build_chat_messages(history)

    assert messages == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "保留这条"},
    ]
