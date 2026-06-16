from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    primary_llm_url: str = "http://localhost:8000/mock/primary"
    candidate_llm_url: str = "http://localhost:8000/mock/candidate"
    primary_timeout_seconds: float = 5.0
    candidate_timeout_seconds: float = 10.0
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379"

    model_config = {"env_file": ".env"}


settings = Settings()
