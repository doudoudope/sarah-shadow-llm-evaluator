from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    primary_llm_url: str = "http://localhost:8000/mock/primary"
    candidate_llm_url: str = "http://localhost:8000/mock/candidate"
    candidate_timeout_seconds: float = 10.0
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
