
# server/app.py — OpenEnv spec entry point
import uvicorn
from main import app


def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)


__all__ = ["app", "main"]