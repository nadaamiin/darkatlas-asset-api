from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # The connection string to PostgreSQL
    database_url: str = "postgresql://assetuser:assetpass@localhost/assetdb"
    # The API key for the application
    api_key: str = "dev-secret-key"
    # Whether to run in debug mode
    debug: bool = True

    class Config:
        env_file = ".env"

# Create an instance of the Settings class to access the configuration values
settings = Settings()