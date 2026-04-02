"""Configurações centrais do backend."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    DATABASE_URL: str = "postgresql://banco_precos:banco_precos@localhost:5435/bancodeprecos"
    APP_NAME: str = "Banco de Preços"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
