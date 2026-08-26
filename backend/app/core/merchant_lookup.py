"""Curated lookup table mapping raw merchant-name substrings (as they tend to
appear in bank/card statements) to a canonical merchant name and category.

Bank statement descriptors are notoriously inconsistent (processor prefixes,
store numbers, billing-entity names that don't match the consumer brand), so
exact string matching alone misses well-known recurring merchants. This table
handles the common cases directly; anything not covered falls through to the
fuzzy-matching + cleanup pipeline in normalize.py.
"""

from __future__ import annotations

# key: a substring that reliably appears in the raw descriptor (case-insensitive)
# value: (canonical_name, category)
KNOWN_MERCHANTS: dict[str, tuple[str, str]] = {
    "netflix": ("Netflix", "streaming"),
    "nflx": ("Netflix", "streaming"),
    "spotify": ("Spotify", "streaming"),
    "hulu": ("Hulu", "streaming"),
    "disney plus": ("Disney+", "streaming"),
    "disneyplus": ("Disney+", "streaming"),
    "hbo max": ("HBO Max", "streaming"),
    "hbomax": ("HBO Max", "streaming"),
    "youtube premium": ("YouTube Premium", "streaming"),
    "youtubepremium": ("YouTube Premium", "streaming"),
    "amazon prime": ("Amazon Prime", "shopping"),
    "prime video": ("Amazon Prime", "shopping"),
    "apple.com/bill": ("Apple Services", "software"),
    "apple music": ("Apple Music", "streaming"),
    "icloud": ("iCloud Storage", "software"),
    "google storage": ("Google One", "software"),
    "google one": ("Google One", "software"),
    "google *": ("Google Services", "software"),
    "dropbox": ("Dropbox", "software"),
    "adobe": ("Adobe Creative Cloud", "software"),
    "microsoft365": ("Microsoft 365", "software"),
    "microsoft 365": ("Microsoft 365", "software"),
    "msft": ("Microsoft 365", "software"),
    "planet fitness": ("Planet Fitness", "fitness"),
    "planetfitness": ("Planet Fitness", "fitness"),
    "la fitness": ("LA Fitness", "fitness"),
    "equinox": ("Equinox", "fitness"),
    "peloton": ("Peloton", "fitness"),
    "classpass": ("ClassPass", "fitness"),
    "nyt": ("New York Times", "news"),
    "nytimes": ("New York Times", "news"),
    "new york times": ("New York Times", "news"),
    "wsj": ("Wall Street Journal", "news"),
    "audible": ("Audible", "media"),
    "kindle unlimited": ("Kindle Unlimited", "media"),
    "linkedin": ("LinkedIn Premium", "professional"),
    "chatgpt": ("ChatGPT Plus", "software"),
    "openai": ("OpenAI", "software"),
    "anthropic": ("Anthropic", "software"),
    "notion": ("Notion", "software"),
    "figma": ("Figma", "software"),
    "github": ("GitHub", "software"),
    "slack": ("Slack", "software"),
    "zoom.us": ("Zoom", "software"),
    "doordash dashpass": ("DoorDash DashPass", "delivery"),
    "instacart+": ("Instacart+", "delivery"),
    "instacart express": ("Instacart+", "delivery"),
}


def lookup_known_merchant(raw_description: str) -> tuple[str, str] | None:
    """Return (canonical_name, category) if the description matches a known
    merchant substring, else None."""
    text = raw_description.lower()
    for key, value in KNOWN_MERCHANTS.items():
        if key in text:
            return value
    return None
