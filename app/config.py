from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str = "shortener"
    postgres_password: str = "shortener_pass"
    postgres_db: str = "shortener_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
