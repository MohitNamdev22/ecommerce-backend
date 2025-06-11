from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    BREVO_API_KEY: str
    FROM_EMAIL: str
    BREVO_SMTP_LOGIN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()