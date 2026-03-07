"""Qt signal/slot helpers."""

from __future__ import annotations

import functools
import logging
import traceback
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable


def safe_slot(func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap one Qt slot so unexpected exceptions are logged instead of bubbling."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return func(self, *args, **kwargs)
        except Exception:
            tb = traceback.format_exc()
            logger.error("Exception in %s:\n%s", func.__name__, tb)
            if hasattr(self, "log"):
                self.log(f"ERROR in {func.__name__}: {tb}")
            return None

    return wrapper
