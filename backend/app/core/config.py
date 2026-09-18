from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    local_papers_path: str = "/workspace/Paper"
    local_notes_path: str = "/workspace/Memo"
    crossref_mailto: str | None = None
    environment: str = "development"
    allowed_hosts: str = "localhost,127.0.0.1,testserver,*.ts.net"

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    # Support both common local entry points:
    #   repository root: backend/.venv/bin/python ...
    #   backend/:        .venv/bin/python ...
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")


settings = Settings()
