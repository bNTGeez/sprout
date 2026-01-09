"""Comprehensive tests for category API routes.

Test coverage:
1. Auth requirements (if applicable)
2. GET /api/categories response shape
3. Ordering and consistency
4. Field handling (icon, color nullability)
"""

import pytest
from sqlalchemy.orm import Session

from app.db.models import User, Category


@pytest.fixture
def user_a(db_session: Session) -> User:
    """Create User A."""
    user = User(email="user_a@example.com", name="User A", password_hash="hash_a")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def diverse_categories(db_session: Session) -> list[Category]:
    """Create diverse categories for testing.
    
    Categories are global (not user-scoped), so they're shared across all users.
    """
    categories = [
        Category(name="Dining", icon="🍽️", color="#FF5733"),
        Category(name="Shopping", icon="🛍️", color="#33FF57"),
        Category(name="Transport", icon="🚗", color="#3357FF"),
        Category(name="Utilities", icon="⚡", color="#FFB533"),
        Category(name="Entertainment", icon="🎬", color="#FF33F5"),
        # Category with no icon/color
        Category(name="Uncategorized", icon=None, color=None),
        # Category with icon but no color
        Category(name="Healthcare", icon="🏥", color=None),
        # Category with color but no icon
        Category(name="Education", icon=None, color="#33FFF5"),
    ]
    
    for cat in categories:
        db_session.add(cat)
    db_session.commit()
    for cat in categories:
        db_session.refresh(cat)
    return categories


# ============================================================================
# 1. AUTH REQUIREMENTS
# ============================================================================

def test_categories_public_endpoint(client, diverse_categories):
    """Categories endpoint is public (does not require authentication).
    
    Categories are global/shared, so they don't require auth.
    If you want to lock it down, add get_current_user dependency to the route.
    """
    response = client.get("/api/categories")
    # Categories are public, should return 200 without auth
    assert response.status_code == 200


def test_categories_accessible_with_auth(authed_client, diverse_categories):
    """Categories accessible with valid auth."""
    response = authed_client.get("/api/categories")
    assert response.status_code == 200


# ============================================================================
# 2. RESPONSE SHAPE
# ============================================================================

def test_list_response_is_array(authed_client, diverse_categories):
    """Response is an array of category objects."""
    response = authed_client.get("/api/categories")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 8  # diverse_categories has 8 categories


def test_category_fields(authed_client, diverse_categories):
    """Each category has expected fields."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    if data:
        cat = data[0]
        required_fields = ["id", "name", "icon", "color"]
        for field in required_fields:
            assert field in cat, f"Missing field: {field}"


def test_category_field_types(authed_client, diverse_categories):
    """Field types are correct."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    for cat in data:
        assert isinstance(cat["id"], int)
        assert isinstance(cat["name"], str)
        # icon and color can be null or string
        assert cat["icon"] is None or isinstance(cat["icon"], str)
        assert cat["color"] is None or isinstance(cat["color"], str)


# ============================================================================
# 3. ORDERING AND CONSISTENCY
# ============================================================================

def test_categories_sorted_by_name(authed_client, diverse_categories):
    """Categories are sorted by name ascending."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    names = [cat["name"] for cat in data]
    assert names == sorted(names)


def test_categories_order_stable(authed_client, diverse_categories):
    """Multiple requests return categories in same order."""
    response1 = authed_client.get("/api/categories")
    response2 = authed_client.get("/api/categories")
    
    data1 = response1.json()
    data2 = response2.json()
    
    ids1 = [cat["id"] for cat in data1]
    ids2 = [cat["id"] for cat in data2]
    
    assert ids1 == ids2


# ============================================================================
# 4. FIELD HANDLING (ICON, COLOR NULLABILITY)
# ============================================================================

def test_category_with_icon_and_color(authed_client, diverse_categories):
    """Categories with both icon and color are returned correctly."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    dining = [cat for cat in data if cat["name"] == "Dining"]
    assert len(dining) == 1
    assert dining[0]["icon"] == "🍽️"
    assert dining[0]["color"] == "#FF5733"


def test_category_with_null_icon_and_color(authed_client, diverse_categories):
    """Categories with null icon and color are returned correctly."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    uncategorized = [cat for cat in data if cat["name"] == "Uncategorized"]
    assert len(uncategorized) == 1
    assert uncategorized[0]["icon"] is None
    assert uncategorized[0]["color"] is None


def test_category_with_icon_no_color(authed_client, diverse_categories):
    """Categories with icon but no color are returned correctly."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    healthcare = [cat for cat in data if cat["name"] == "Healthcare"]
    assert len(healthcare) == 1
    assert healthcare[0]["icon"] == "🏥"
    assert healthcare[0]["color"] is None


def test_category_with_color_no_icon(authed_client, diverse_categories):
    """Categories with color but no icon are returned correctly."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    education = [cat for cat in data if cat["name"] == "Education"]
    assert len(education) == 1
    assert education[0]["icon"] is None
    assert education[0]["color"] == "#33FFF5"


# ============================================================================
# 5. GLOBAL SCOPE (NOT USER-SPECIFIC)
# ============================================================================

def test_categories_are_global(
    app, client, db_session,
    user_a: User, diverse_categories
):
    """Categories are global - same categories visible to all users.
    
    This test verifies that categories are NOT user-scoped.
    """
    # Create second user
    user_b = User(email="user_b@example.com", name="User B", password_hash="hash_b")
    db_session.add(user_b)
    db_session.commit()
    
    from app.core.auth import get_current_user
    
    # Get categories as User A
    app.dependency_overrides[get_current_user] = lambda: user_a
    response_a = client.get("/api/categories")
    data_a = response_a.json()
    
    # Get categories as User B
    app.dependency_overrides[get_current_user] = lambda: user_b
    response_b = client.get("/api/categories")
    data_b = response_b.json()
    
    # Should be identical
    assert len(data_a) == len(data_b)
    
    ids_a = {cat["id"] for cat in data_a}
    ids_b = {cat["id"] for cat in data_b}
    assert ids_a == ids_b


# ============================================================================
# 6. EDGE CASES
# ============================================================================

def test_empty_categories_list(app, client, db_session):
    """Returns empty list when no categories exist.
    
    Note: This test is isolated - it creates a fresh DB session that gets
    rolled back, so it won't affect other tests.
    """
    # Since we're in a test transaction that rolls back, deleting categories
    # here won't affect other tests
    db_session.query(Category).delete()
    db_session.commit()
    
    response = client.get("/api/categories")
    assert response.status_code == 200
    
    data = response.json()
    assert data == []


def test_category_name_uniqueness(authed_client, db_session):
    """Category names should be unique (or at least distinguishable)."""
    # Create categories with similar names
    cat1 = Category(name="Test Category", icon="🧪", color="#FF0000")
    cat2 = Category(name="Test Category 2", icon="🧪", color="#00FF00")
    db_session.add_all([cat1, cat2])
    db_session.commit()
    
    response = authed_client.get("/api/categories")
    data = response.json()
    
    test_cats = [cat for cat in data if "Test Category" in cat["name"]]
    assert len(test_cats) == 2
    
    # Each should have distinct ID
    ids = [cat["id"] for cat in test_cats]
    assert len(ids) == len(set(ids))


def test_emoji_icons_rendered_correctly(authed_client, diverse_categories):
    """Emoji icons are returned as-is (UTF-8)."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    # Check that emojis are preserved
    shopping = [cat for cat in data if cat["name"] == "Shopping"]
    assert len(shopping) == 1
    assert shopping[0]["icon"] == "🛍️"


def test_hex_color_format(authed_client, diverse_categories):
    """Colors are returned in hex format."""
    response = authed_client.get("/api/categories")
    data = response.json()
    
    for cat in data:
        if cat["color"]:
            # Should start with # and be 7 chars (or 4 for short format)
            assert cat["color"].startswith("#")
            assert len(cat["color"]) in [4, 7]


# ============================================================================
# 7. PERFORMANCE / CACHING CONSIDERATIONS
# ============================================================================

def test_categories_cacheable(authed_client, diverse_categories):
    """Categories can be cached (response consistent across calls).
    
    Since categories are global and rarely change, they're good candidates
    for client-side caching.
    """
    response1 = authed_client.get("/api/categories")
    response2 = authed_client.get("/api/categories")
    
    assert response1.json() == response2.json()
