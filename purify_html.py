import re

import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "b",
    "i",
    "ul",
    "ol",
    "li",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "a",
    "img",
    "pre",
    "code",
    "span",
    "div",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "span": ["class"],
    "div": ["class"],
    "blockquote": ["class"],
    "p": ["class"],
    "h2": ["class"],
    "h3": ["class"],
    "h4": ["class"],
    "pre": ["class"],
    "code": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]


def purify_html(html: str) -> str:
    """Sanitize HTML to prevent XSS while preserving formatting."""
    if not html:
        return ""
    html = re.sub(
        r"<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>", "", html, flags=re.I | re.S
    )
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
