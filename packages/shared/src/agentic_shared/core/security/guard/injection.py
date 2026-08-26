from __future__ import annotations

import re

_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?(previous|prior|above)\s+instructions"
    r"|disregard\s+(the\s+)?(system|above)"
    r"|you\s+are\s+now"
    r"|new\s+system\s+prompt"
    r"|jailbreak"
    r"|<\s*/?\s*system\s*>"
    r"|```\s*system"
    r"|repeat\s+(the\s+)?(system|hidden)\s+prompt"
    r"|reveal\s+(your\s+)?(system|hidden)\s+prompt"
    r"|developer\s+mode\s+enabled"
    r"|DAN\s+mode)",
    re.IGNORECASE,
)


def looks_like_prompt_injection(text: str) -> bool:
    return bool(_INJECTION_PATTERNS.search(text))
