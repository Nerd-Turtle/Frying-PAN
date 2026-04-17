from app.core.config import Settings


def test_default_database_url_targets_postgresql() -> None:
    settings = Settings()

    assert settings.database_url.startswith("postgresql+psycopg://")


def test_default_cors_origins_are_split_cleanly() -> None:
    settings = Settings(cors_origins="http://localhost:3000, http://localhost:3001")

    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
