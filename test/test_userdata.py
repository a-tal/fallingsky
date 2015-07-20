import pytest

from fallingsky.user import UserData


def test_object_item_access():
    """Ensure we can set and retrieve user data as dict keys."""

    user_data = UserData(1)
    user_data["test_key"] = True
    assert user_data["test_key"] is True
    user_data["test_key"] = ["one", "two", "three"]
    assert user_data.get("test_key") == ["one", "two", "three"]
    assert user_data.get("ToTaLLy_PR0B4blY_N07_R34L") is None
    assert user_data.get("ToTaLLy_PR0B4blY_N07_R34L", "kay") == "kay"


if __name__ == "__main__":
    pytest.main(["-rx", "-vv", "--pdb", __file__])
