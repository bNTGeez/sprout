"""Prompts for agents."""

MERCHANT_NORMALIZATION_PROMPT = """You normalize merchant names from transactions.

Rules:
- Remove store numbers, locations, payment prefixes (TST*, SQ*)
- Remove .COM, .NET suffixes
- Use Title Case
- Keep brand recognizable

Examples:
"STARBUCKS #12345" → "Starbucks"
"AMZN MKTPLACE" → "Amazon"
"TST* COFFEE SHOP" → "Coffee Shop"

Return structured output with normalized_merchant and confidence."""

def get_classification_prompt(categories: list[str]) -> str:
    cats = ", ".join(categories)
    return f"""You categorize transactions into one of: {cats}

Rules:
- Match merchant to category
- Detect subscriptions (recurring monthly charges)
- Add 1-3 simple tags
- Use "Other" if uncertain

Return structured output with category_name, is_subscription, tags, confidence."""