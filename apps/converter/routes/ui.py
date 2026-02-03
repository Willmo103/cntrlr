# TODO: Test UI for this module
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from config import app_settings

templates = Jinja2Templates(
    directory=str(app_settings.app_root / "apps" / "converter" / "templates")
)


ui_router = APIRouter(prefix="/ui", tags=["ui"])


@ui_router.get("/", summary="Converter UI Home")
async def converter_ui_home(request):
    """Renders the home page for the Converter UI."""
    return templates.TemplateResponse(
        "converter_home.html",
        {"request": request, "app_name": "Converter UI"},
    )
