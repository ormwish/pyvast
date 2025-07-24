
import re, time, uuid, random, hashlib
from datetime import datetime
from typing import Dict, Any

PATTERN = re.compile(r'\[([A-Z0-9_]+)]|\${([A-Z0-9_]+)}|%%([A-Z0-9_]+)%%|\$\$([A-Z0-9_]+)\$\$', re.I)

def _cache_bust():
    return str(int(time.time()*1000))

_BUILTIN = {
    'TIMESTAMP': lambda: int(time.time()),
    'CACHE_BUST': _cache_bust,
    'CACHEBUSTER': _cache_bust,
    'UUID': lambda: str(uuid.uuid4()),
}

def interpolate_macros(text: str, ctx: Dict[str, Any]) -> str:
    if not isinstance(text, str):
        return text
    def repl(m):
        key = next(g for g in m.groups() if g)
        k_up = key.upper()
        if k_up in _BUILTIN:
            return str(_BUILTIN[k_up]())
        for variant in (key, k_up, key.lower()):
            if variant in ctx:
                return str(ctx[variant])
        return m.group(0)
    return PATTERN.sub(repl, text)
