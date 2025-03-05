from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  MONGODB: str
  SLACK_BOT_KEY: str

  model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
