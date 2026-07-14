from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeInfo:
    name: str
    label: str


def detect_runtime() -> RuntimeInfo:
    if os.getenv("STREAMLIT_CLOUD"):
        return RuntimeInfo(name="streamlit-cloud", label="Runtime: streamlit-cloud")
    return RuntimeInfo(name="local", label="Runtime: local")
