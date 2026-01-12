"""Configuration management for the routing table API service."""

import os


class Settings:
    """Application settings with environment variable support."""

    def __init__(self):
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "5000"))
        self.proc_num: int = int(os.getenv("PROC_NUM", "5"))
        self.routes_file: str = os.getenv("ROUTES_FILE", "routes.txt")
        self.max_metric: int = int(os.getenv("MAX_METRIC", "32768"))  # 0x8000

    def __repr__(self) -> str:
        return (
            f"Settings(host={self.host}, port={self.port}, "
            f"proc_num={self.proc_num}, routes_file={self.routes_file})"
        )


settings = Settings()
