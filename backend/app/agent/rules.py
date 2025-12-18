from typing import Optional

KNOWN_MERCHANT_PATTERNS = {
    "STARBUCKS": "Starbucks",
    "AMZN": "Amazon",
    "AMAZON": "Amazon",
    "NETFLIX": "Netflix",
    "UBER": "Uber",
    "WHOLEFDS": "Whole Foods",
    "WALMART": "Walmart",
    "TARGET": "Target",
    "SPOTIFY": "Spotify",
    # can add more later
}


def normalize_merchant_rule_based(raw_merchant: str) -> Optional[str]:
    """Fast pattern matching for known merchants."""
    if not raw_merchant:
        return None
    upper = raw_merchant.upper()
    for pattern, normalized in KNOWN_MERCHANT_PATTERNS.items():
        if pattern in upper:
            return normalized
    return None


def clean_merchant_fallback(raw_merchant: str) -> str:
    """Basic cleanup when all else fails."""
    if not raw_merchant:
        return "Unknown Merchant"
    cleaned = raw_merchant
    # Remove payment processor prefixes
    for prefix in ["TST*", "SQ*", "SP*", "PP*"]:
        if cleaned.upper().startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    # Title case
    return cleaned.title() or "Unknown Merchant"

KNOWN_MERCHANT_CATEGORIES = {
    "Starbucks": ("Dining", False),
    "Netflix": ("Subscriptions", True),
    "Spotify": ("Subscriptions", True),
    "Uber": ("Transportation", False),
    "Whole Foods": ("Groceries", False),
    "Amazon": ("Shopping", False),
    # can add more later
}


def categorize_transaction_rule_based(
    merchant: str,
    amount: float
) -> Optional[tuple[str, bool, list[str]]]:
    """Fast categorization for known merchants."""
    if merchant not in KNOWN_MERCHANT_CATEGORIES:
        return None
    category, is_sub = KNOWN_MERCHANT_CATEGORIES[merchant]
    tags = ["recurring"] if is_sub else []
    tags.append("expense" if amount < 0 else "income")
    return (category, is_sub, tags[:3])


def validate_category_name(category_name: str, valid_categories: list[str]) -> str:
    """Validate category against the list otherwise choose 'Other'.
    """
    if category_name in valid_categories:
        return category_name
    if "Other" in valid_categories:
        return "Other"
    raise ValueError(f"No 'Other' category found.")