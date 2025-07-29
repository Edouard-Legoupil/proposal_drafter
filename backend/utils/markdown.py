#  Standard Library
import re

# This module contains helper functions for handling Markdown conversions.

def convert_markdown_bold(text: str) -> str:
    """
    Safely converts Markdown-style bold text (e.g., "**text**")
    to HTML-style bold tags (e.g., "<b>text</b>").

    This is primarily used for preparing text for libraries like ReportLab
    that can render simple HTML tags.

    Args:
        text: The input string containing Markdown bold syntax.

    Returns:
        A string with Markdown bold syntax replaced by HTML bold tags.
    """
    if not text:
        return ""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
