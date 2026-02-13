import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sweetwatch import __version__
from sweetwatch.api.routers.glucose import router as glucose_router
from sweetwatch.db.engine import engine
from sweetwatch.models.glucose import Base
from sweetwatch.tasks.sync import lifespan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SweetWatch API",
    version=__version__,
    description="CGM monitoring with AI agent and Garmin integration",
    lifespan=lifespan,
)

# Include routers
app.include_router(glucose_router)

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Serve the main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})
