import os


class ConfigVariables:
    # Database variables
    MONGO_URI: str = os.getenv("MONGO_URI")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")

    # Google Auth variables
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")

    # JWT Auth variables
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: str = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
