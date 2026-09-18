import os


# Tests do not need a running database or a private .env file.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
