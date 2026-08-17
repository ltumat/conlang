from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Conlang API"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://conlang:conlang@localhost:5432/conlang"
    )

    model_config = {"env_file": ".env"}


settings = Settings()
