from fastapi import FastAPI

from sweetwatch import __version__

app = FastAPI(
    title="SweetWatch API",
    version=__version__,
    description="CGM monitoring with AI agent and Garmin integration",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
