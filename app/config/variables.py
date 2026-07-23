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

    # Cloudfare R2 envs
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY")
    R2_ENDPOINT: str = os.getenv("R2_ENDPOINT")
    R2_BUCKET: str = os.getenv("R2_BUCKET")
    R2_REGION: str = os.getenv("R2_REGION")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL")

    # Redis envs
    REDIS_URL: str = os.getenv("REDIS_URL")

    # Magic envs
    MAGIC_LINK: str = os.getenv("MAGIC_LINK")

    # Environment envs
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
