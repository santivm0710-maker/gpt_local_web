import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_database_path() -> Path:
    if os.getenv("LOCALAPPDATA"):
        data_dir = Path(os.environ["LOCALAPPDATA"])
    else:
        data_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data_dir / "ChatLocal" / "chat.sqlite3"


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    database_path: Path = field(default_factory=_default_database_path)
    host: str = "127.0.0.1"
    port: int = 8000
    chat_model: str = "llama3.2:3b"
    chat_history_limit: int = 20
    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    max_body: int = 64 * 1024
    max_image_prompt: int = 2000
    max_image_bytes: int = 10 * 1024 * 1024
    image_timeout_seconds: int = 120

    @classmethod
    def load(cls) -> "AppConfig":
        base_dir = Path(__file__).resolve().parent.parent
        cls._load_env_file(base_dir / ".env")
        database_path = os.getenv("DATABASE_PATH", "").strip()
        if database_path:
            database_path = os.path.expandvars(database_path)
            resolved_database_path = Path(database_path).expanduser()
            if not resolved_database_path.is_absolute():
                resolved_database_path = base_dir / resolved_database_path
        else:
            resolved_database_path = _default_database_path()
        return cls(
            base_dir=base_dir,
            database_path=resolved_database_path,
            cloudflare_account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip(),
            cloudflare_api_token=os.getenv("CLOUDFLARE_API_TOKEN", "").strip(),
        )

    @staticmethod
    def _load_env_file(env_file: Path):
        """Carga valores de .env sin reemplazar variables definidas en el sistema."""
        if not env_file.is_file():
            return
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if name:
                os.environ.setdefault(name, value)
