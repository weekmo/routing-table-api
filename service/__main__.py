"""Entry point for running the service as a module."""

import uvicorn
from service.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "service.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.proc_num
    )
