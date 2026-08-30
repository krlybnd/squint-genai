from __future__ import annotations

import sys
from pathlib import Path

_KC_TEST_ROOT = Path(__file__).resolve().parent
if str(_KC_TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(_KC_TEST_ROOT))

from support import install_keycloak_stubs  # noqa: E402

install_keycloak_stubs()
