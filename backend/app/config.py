from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Conlang API"
    debug: bool = False
    database_url: str = "sqlite:///./conlang.db"

    model_config = {"env_file": ".env"}


settings = Settings()
