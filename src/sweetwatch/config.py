from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CGM Source
    cgm_source: str = "nightscout"  # "nightscout" or "librelinkup"

    # Nightscout
    nightscout_url: str = ""
    nightscout_api_secret: str = ""

    # LibreLinkUp
    libre_username: str = ""
    libre_password: str = ""
    libre_region: str = "EU"

    # Claude API
    anthropic_api_key: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    # Database
    database_url: str = "sqlite:///./sweetwatch.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
