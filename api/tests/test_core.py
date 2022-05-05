import os

from app.core.hashing import Hasher


def test_config_read(monkeypatch):
    monkeypatch.setenv("ALERTS_TOPIC", "alert_test")
    monkeypatch.setenv("SECRET_KEY", "randomkey")

    # import after to modify ENV values
    from app.core.config import Settings
    settings = Settings()

    assert settings.ALERTS_TOPIC == "alert_test"
    assert settings.SECRET_KEY == "randomkey"


def test_hasher_verify_password():
    password = "supersecretpassword"
    expected_hash = Hasher.get_password_hash(password)

    assert Hasher.verify_password(password, expected_hash)
    assert not Hasher.verify_password("anotherpasswd", expected_hash)
    assert not Hasher.verify_password(password, "$2b$12$GxbBjHl9j8hK5YxMw1Qyle4IIaKOYihP7wyjkujC0amURrWoafMB.")
