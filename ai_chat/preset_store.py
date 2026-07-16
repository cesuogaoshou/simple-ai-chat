from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ai_chat.presets import PromptPreset

CUSTOM_PRESET_ID_PREFIX = "custom_"
CUSTOM_PRESET_DESCRIPTION = "Custom prompt preset."
DEFAULT_CUSTOM_PRESET_NAME = "Custom preset"


@dataclass(frozen=True)
class CustomPromptPreset:
    id: str
    name: str
    description: str
    system_prompt: str
    created_at: str
    updated_at: str


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_custom_preset_id(preset_id: str) -> bool:
    return preset_id.startswith(CUSTOM_PRESET_ID_PREFIX)


def safe_custom_name(name: str) -> str:
    cleaned = name.strip()
    return cleaned or DEFAULT_CUSTOM_PRESET_NAME


def new_custom_preset_id(existing_ids: set[str]) -> str:
    while True:
        preset_id = f"{CUSTOM_PRESET_ID_PREFIX}{uuid4()}"
        if preset_id not in existing_ids:
            return preset_id


def create_custom_preset(
    name: str, system_prompt: str, existing_ids: set[str]
) -> CustomPromptPreset | None:
    prompt = system_prompt.strip()
    if not prompt:
        return None
    now = utc_now()
    return CustomPromptPreset(
        id=new_custom_preset_id(existing_ids),
        name=safe_custom_name(name),
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt=prompt,
        created_at=now,
        updated_at=now,
    )


def custom_preset_to_dict(preset: CustomPromptPreset) -> dict[str, str]:
    return {
        "id": preset.id,
        "name": preset.name,
        "description": preset.description,
        "system_prompt": preset.system_prompt,
        "created_at": preset.created_at,
        "updated_at": preset.updated_at,
    }


def custom_preset_from_dict(
    data: dict[str, object], existing_ids: set[str], reserved_ids: set[str]
) -> CustomPromptPreset | None:
    prompt = str(data.get("system_prompt", "")).strip()
    if not prompt:
        return None

    preset_id = str(data.get("id", "")).strip()
    if (
        not is_custom_preset_id(preset_id)
        or preset_id in existing_ids
        or preset_id in reserved_ids
    ):
        preset_id = new_custom_preset_id(existing_ids | reserved_ids)

    now = utc_now()
    return CustomPromptPreset(
        id=preset_id,
        name=safe_custom_name(str(data.get("name", ""))),
        description=str(data.get("description") or CUSTOM_PRESET_DESCRIPTION),
        system_prompt=prompt,
        created_at=str(data.get("created_at") or now),
        updated_at=str(data.get("updated_at") or now),
    )


def load_custom_presets(path: Path, reserved_ids: set[str]) -> list[CustomPromptPreset]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_name(f"{path.stem}.invalid{path.suffix}")
        path.replace(backup)
        return []

    raw_presets = payload.get("presets", []) if isinstance(payload, dict) else []
    presets = []
    seen_ids: set[str] = set()
    for raw_preset in raw_presets:
        if isinstance(raw_preset, dict):
            preset = custom_preset_from_dict(raw_preset, seen_ids, reserved_ids)
            if preset is not None:
                presets.append(preset)
                seen_ids.add(preset.id)
    return presets


def save_custom_presets(path: Path, presets: list[CustomPromptPreset]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"presets": [custom_preset_to_dict(preset) for preset in presets]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_custom_preset(
    presets: list[CustomPromptPreset], preset_id: str
) -> list[CustomPromptPreset]:
    return [preset for preset in presets if preset.id != preset_id]


def custom_to_prompt_preset(preset: CustomPromptPreset) -> PromptPreset:
    return PromptPreset(
        id=preset.id,
        name=preset.name,
        description=preset.description,
        system_prompt=preset.system_prompt,
    )
