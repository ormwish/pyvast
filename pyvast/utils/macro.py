"""
pyvast.utils.macro
~~~~~~~~~~~~~~~~~~

Простой интерполятор макросов для PyVAST.

Поддерживаемые формы:

* `[MACRO]`                        – AdWords-стиль квадратных скобок
* `${MACRO}` / `${path.with.dots}` – VAST / VAST-like шаблоны
* `%%MACRO%%`
* `$$MACRO$$`

Особенности
-----------

* Встроенные функции (`CACHE_BUST`, `TIMESTAMP`, `UUID` …).
* Поддержка «точечных путей» – `${self.owner_id}` ищет
  `ctx["self"]["owner_id"]`.
* Регистронезависим (сначала ищем точное совпадение, затем upper/lower).
"""

from __future__ import annotations

import random
import re
import time
import uuid
from datetime import datetime
from typing import Any, Dict

# ──────────────────────────────────────────────────────────────────────────────
#  Регэксп: 5 групп, одна из них сработает → берём непустую.
#           В ⧼{{ }}⧽ поддерживаем точки и подчёркивания.
PATTERN = re.compile(
    r"\[([A-Z0-9_.]+)]|"          # [MACRO] или [self.owner_id]
    r"\${([^}]+)}|"               # ${MACRO} или ${self.owner_id}
    r"%%([A-Z0-9_]+)%%|"          # %%MACRO%%
    r"\$\$([A-Z0-9_]+)\$\$|"      # $$MACRO$$
    r"{{\s*([A-Z0-9_.]+)\s*}}",   # {{ self.owner_id }}
    re.I,
)

# ──────────────────────────────────────────────────────────────────────────────
#  Встроенные функции-генераторы

def _cache_bust() -> str:
    # Use time + random to ensure uniqueness even in rapid succession
    return str(int(time.time() * 1000)) + str(random.randint(100, 999))


_BUILTIN: Dict[str, Any] = {
    "TIMESTAMP": lambda: int(datetime.utcnow().timestamp()),
    "CACHE_BUST": _cache_bust,
    "CACHEBUSTER": _cache_bust,
    "UUID": lambda: str(uuid.uuid4()),
    "RANDOM_INT": lambda: random.randint(1, 999_999),
}

# ──────────────────────────────────────────────────────────────────────────────
#  Вспом. получение «точечного» пути из словаря

def _dotted_get(path: str, src: Dict[str, Any]) -> Any | None:
    cur: Any = src
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


# ──────────────────────────────────────────────────────────────────────────────
#  Основная функция

def interpolate_macros(text: str, ctx: Dict[str, Any]) -> str:
    """
    Заменяет макросы внутри `text` на значения из `ctx`
    или на результаты встроенных функций.
    """

    if not text or not isinstance(text, str):
        return text

    def _replace(match: re.Match) -> str:
        # берём первое непустое совпадение из 5 групп
        raw_key = next(g for g in match.groups() if g)
        key = raw_key.strip()
        key_upper = key.upper()

        # 1) встроенные функции
        if key_upper in _BUILTIN:
            try:
                return str(_BUILTIN[key_upper]())
            except Exception:
                return f"<ERR:{key_upper}>"

        # 2) прямое совпадение ключа в корне ctx
        for variant in (key, key_upper, key.lower()):
            if variant in ctx:
                return str(ctx[variant])

        # 3) dotted-path lookup  (self.owner_id → ctx['self']['owner_id'])
        val = _dotted_get(key, ctx) or _dotted_get(key.lower(), ctx)
        if val is not None:
            return str(val)

        # 4) не найдено
        return match.group(0)  # оставляем как есть

    return PATTERN.sub(_replace, text)


# ──────────────────────────────────────────────────────────────────────────────
#  Быстрый helper для единичных вызовов

def interpolate(text: str, *, context: Dict[str, Any] | None = None) -> str:
    """
    Alias для `interpolate_macros`, чтобы меньше писать.
    """
    return interpolate_macros(text, context or {})