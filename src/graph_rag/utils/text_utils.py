"""Text utility functions."""

import re
from typing import Optional, Tuple


def parse_orig_tags(text: str) -> Tuple[str, Optional[str]]:
    """Parse <orig> tags and return (display_text, original_text).

    Args:
        text: Text potentially containing <orig> tags

    Returns:
        Tuple of (display_text, original_text) where original_text is None if no tag found
    """
    match = re.search(r"(.*?)\s*<orig>(.*?)</orig>", text, re.DOTALL)
    if match:
        display_text = match.group(1).strip()
        original_text = match.group(2).strip()
        return display_text, original_text
    return text, None


def strip_orig_tags(text: str) -> str:
    """Remove <orig> tags from text, keeping only the display text.

    Args:
        text: Text potentially containing <orig> tags

    Returns:
        Text with <orig> tags removed
    """
    return re.sub(r"\s*<orig>.*?</orig>", "", text, flags=re.DOTALL).strip()

