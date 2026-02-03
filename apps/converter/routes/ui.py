# TODO: Test UI for this module
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from config import app_root

templates = Jinja2Templates(directory=(app_root / "templates").resolve().as_posix())

ui_router = APIRouter(prefix="/ui", tags=["ui"])


@ui_router.get("/", summary="UI Root")
async def ui_root(request: Request):
    """Root endpoint for the UI."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "Converter UI is operational."},
    )
