import pytest

from app.agent.rules import (
    normalize_merchant_rule_based,
    clean_merchant_fallback,
    categorize_transaction_rule_based,
    validate_category_name,
    detect_subscription_pattern,
)

"""
Arrange - Set up test data
Act - Call the function
Assert - Check the result
"""

class TestNormalizeMerchantRuleBased:

  def test_known_pattern_starbucks(self):

    # Arrange
    raw = "STARBUCKS #12345"

    # Act
    result = normalize_merchant_rule_based(raw)

    # Assert
    assert result == "Starbucks"

  def test_case_insensitive_matching(self):

    raw = "starbucks store"
    result = normalize_merchant_rule_based(raw)
    assert result == "Starbucks"

  def test_unknown_pattern(self):

    raw = "RANDOM COFFEE"
    result = normalize_merchant_rule_based(raw)
    assert result is None 

  def test_empty_string(self):

    raw = ""
    result = normalize_merchant_rule_based(raw)
    assert result is None

  def test_amazon_pattern(self):

    raw = "AMZN MKTPLACE"
    result = normalize_merchant_rule_based(raw)
    assert result == "Amazon"

  def test_amazon_pattern_full(self):

    raw = "AMAZON.COM"
    result = normalize_merchant_rule_based(raw)
    assert result == "Amazon"

class TestCleanMerchantFallback: 

  def test_removes_tst_prefix(self):

    # Arrange
    raw = "TST* COFFEE SHOP"

    # Act 
    result = clean_merchant_fallback(raw)

    # Assert
    assert result == "Coffee Shop"

  def test_case_insensitive_matching(self):
    raw = "sq* local bakery"
    result = clean_merchant_fallback(raw)
    assert result == "Local Bakery"

  def test_prefix_only(self):
    raw = "TST*"
    result = clean_merchant_fallback(raw)
    assert result == "Unknown Merchant"

  def test_empty_string(self):
    raw = ""
    result = clean_merchant_fallback(raw)
    assert result == "Unknown Merchant"

  def test_whitespace_only(self):
    raw = "   "
    result = clean_merchant_fallback(raw)
    assert result == "Unknown Merchant"

  def test_title_case(self):
    raw = "random coffee shop"
    result = clean_merchant_fallback(raw)
    assert result == "Random Coffee Shop"

class TestCategorizeTransactionRuleBased:

  def test_categorizes_starbucks_as_dining(self):

    # Arrange
    merchant = "Starbucks"

    # Act
    result = categorize_transaction_rule_based(merchant, -5.50)

    # Assert
    assert result is not None 
    category, is_sub, tags = result
    assert category == "Dining"
    assert is_sub is False
    assert "recurring" not in tags
    assert "expense" in tags

  def test_subscription_merchant(self):
    merchant = "Netflix"
    result = categorize_transaction_rule_based(merchant, -15.99)
    assert result is not None 
    category, is_sub, tags = result 
    assert category == "Subscriptions"
    assert is_sub is True
    assert "recurring" in tags
    assert "expense" in tags

  def test_income_direction(self):
    merchant = "Amazon"
    result = categorize_transaction_rule_based(merchant, 10.0)
    assert result is not None 
    category, is_sub, tags = result 
    assert "income" in tags 

  def test_unknown_merchant(self):
    merchant = "Some Place"
    result = categorize_transaction_rule_based(merchant, -1.0)
    assert result is None


class TestValidateCategoryName: 

  def test_valid_category_passes_through(self):

    # Arrange
    category_name = "Dining"
    valid_categories = ["Dining", "Groceries", "Entertainment", "Other"]
    # Act
    result = validate_category_name(category_name, valid_categories)

    # Assert
    assert result == "Dining"

  def test_invalid_category_fallback(self):
    category_name = "Fake Category"
    valid_categories = ["Dining", "Groceries", "Entertainment", "Other"]
    result = validate_category_name(category_name, valid_categories)
    assert result == "Other"

  def test_no_other_category_raises_error(self):
    valid_categories = ["Dining", "Groceries"]
    with pytest.raises(ValueError, match="No 'Other' category found."):
      validate_category_name("Fake Category", valid_categories)


class TestDetectSubscriptionPattern:

  def test_detects_perfect_monthly_subscription(self):
    """Perfect monthly subscription detected."""
    # Arrange 
    recent_amounts = [-9.99, -9.99, -9.99]
    recent_dates = ["2024-01-15", "2024-02-15", "2024-03-15"]

    # Act
    result = detect_subscription_pattern(recent_amounts, recent_dates)

    # Assert 
    assert result is True

  def test_rejects_inconsistent_amounts(self):
    recent_amounts = [-10.00, -10.51]
    recent_dates = ["2024-01-01", "2024-02-01"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is False

  def test_rejects_weekly_pattern(self):
    recent_amounts = [-10.00, -10.00, -10.00]
    recent_dates = ["2024-01-01", "2024-01-08", "2024-01-15"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is False

  def test_rejects_too_few_transactions(self):
    recent_amounts = [-10.00]
    recent_dates = ["2024-01-01"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is False

  def test_mismatched_dates_and_amounts(self):
    recent_amounts = [-10.00, -10.00, -10.00]
    recent_dates = ["2024-01-01", "2024-01-08"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is False

  def test_invalid_date_format(self):
    recent_amounts = [-10.00, -10.00, -10.00]
    recent_dates = ["invalid", "2024-02-01", "2024-03-01"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is False

  def test_handles_sign(self):
    recent_amounts = [10.00, 10.00, 10.00]
    recent_dates = ["2024-01-01", "2024-02-01", "2024-03-01"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is True

  def test_handles_zero_amounts(self):
    recent_amounts = [0.00, 0.00, 0.00]
    recent_dates = ["2024-01-01", "2024-02-01", "2024-03-01"]

    result = detect_subscription_pattern(recent_amounts, recent_dates)
    assert result is True