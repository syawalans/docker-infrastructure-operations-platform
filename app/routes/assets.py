from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import ASSET_STATUSES, ASSET_TYPES, ENVIRONMENTS
from app.core.database import get_db
from app.schemas.asset import AssetCreate
from app.services.asset_service import asset_service


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("", response_class=HTMLResponse)
def assets_list(
    request: Request,
    q: str | None = None,
    asset_type: str | None = None,
    environment: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    assets = asset_service.search_assets(
        db=db,
        query=q,
        asset_type=asset_type,
        environment=environment,
        status=status,
    )

    return templates.TemplateResponse(
        request=request,
        name="assets/list.html",
        context={
            "page_title": f"Assets - {settings.APP_NAME}",
            "assets": assets,
            "search_query": q or "",
            "selected_asset_type": asset_type or "",
            "selected_environment": environment or "",
            "selected_status": status or "",
            "asset_types": ASSET_TYPES,
            "environments": ENVIRONMENTS,
            "statuses": ASSET_STATUSES,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def asset_create_form(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="assets/form.html",
        context={
            "page_title": f"Add Asset - {settings.APP_NAME}",
            "form_title": "Add Infrastructure Asset",
            "form_description": "Register a new infrastructure asset.",
            "form_action": "/assets/new",
            "submit_label": "Save Asset",
            "asset": None,
            "asset_types": ASSET_TYPES,
            "environments": ENVIRONMENTS,
            "statuses": ASSET_STATUSES,
        },
    )


def render_asset_category(
    request: Request,
    db: Session,
    *,
    title: str,
    description: str,
    asset_types_filter: list[str],
    active_nav: str,
):
    assets = []

    for asset_type in asset_types_filter:
        assets.extend(
            asset_service.search_assets(
                db=db,
                asset_type=asset_type,
            )
        )

    return templates.TemplateResponse(
        request=request,
        name="assets/category.html",
        context={
            "page_title": f"{title} - {settings.APP_NAME}",
            "title": title,
            "description": description,
            "assets": assets,
            "active_nav": active_nav,
        },
    )


@router.get("/servers", response_class=HTMLResponse)
def assets_servers(
    request: Request,
    db: Session = Depends(get_db),
):
    return render_asset_category(
        request,
        db,
        title="Servers",
        description="Physical server infrastructure assets.",
        asset_types_filter=["Server"],
        active_nav="servers",
    )


@router.get("/network", response_class=HTMLResponse)
def assets_network(
    request: Request,
    db: Session = Depends(get_db),
):
    return render_asset_category(
        request,
        db,
        title="Network Devices",
        description="Network infrastructure and connectivity assets.",
        asset_types_filter=[
            "Switch",
            "Router",
            "Firewall",
            "Access Point",
        ],
        active_nav="network",
    )


@router.get("/virtual-machines", response_class=HTMLResponse)
def assets_virtual_machines(
    request: Request,
    db: Session = Depends(get_db),
):
    return render_asset_category(
        request,
        db,
        title="Virtual Machines",
        description="Virtualized infrastructure assets.",
        asset_types_filter=["Virtual Machine"],
        active_nav="virtual-machines",
    )


@router.get("/storage", response_class=HTMLResponse)
def assets_storage(
    request: Request,
    db: Session = Depends(get_db),
):
    return render_asset_category(
        request,
        db,
        title="Storage",
        description="Storage infrastructure assets.",
        asset_types_filter=["Storage"],
        active_nav="storage",
    )


@router.get("/{asset_id}", response_class=HTMLResponse)
def asset_detail(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset(
        db,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="assets/detail.html",
        context={
            "page_title": f"{asset.hostname} - {settings.APP_NAME}",
            "asset": asset,
        },
    )


@router.get("/{asset_id}/edit", response_class=HTMLResponse)
def asset_edit_form(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset(
        db,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="assets/form.html",
        context={
            "page_title": f"Edit {asset.hostname} - {settings.APP_NAME}",
            "form_title": "Edit Infrastructure Asset",
            "form_description": "Update infrastructure asset information.",
            "form_action": f"/assets/{asset.id}/edit",
            "submit_label": "Update Asset",
            "asset": asset,
            "asset_types": ASSET_TYPES,
            "environments": ENVIRONMENTS,
            "statuses": ASSET_STATUSES,
        },
    )


@router.post("/new")
def asset_create(
    name: str = Form(...),
    hostname: str = Form(...),
    asset_type: str = Form(...),
    vendor: str = Form(""),
    model: str = Form(""),
    ip_address: str = Form(...),
    operating_system: str = Form(""),
    environment: str = Form(...),
    location: str = Form(""),
    status: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    asset_data = AssetCreate(
        name=name,
        hostname=hostname,
        asset_type=asset_type,
        vendor=vendor or None,
        model=model or None,
        ip_address=ip_address,
        operating_system=operating_system or None,
        environment=environment,
        location=location or None,
        status=status,
        description=description or None,
    )

    asset_service.create_asset(
        db,
        asset_data,
    )

    return RedirectResponse(
        url="/assets",
        status_code=303,
    )


@router.post("/{asset_id}/edit")
def asset_edit(
    asset_id: int,
    name: str = Form(...),
    hostname: str = Form(...),
    asset_type: str = Form(...),
    vendor: str = Form(""),
    model: str = Form(""),
    ip_address: str = Form(...),
    operating_system: str = Form(""),
    environment: str = Form(...),
    location: str = Form(""),
    status: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    asset_data = AssetCreate(
        name=name,
        hostname=hostname,
        asset_type=asset_type,
        vendor=vendor or None,
        model=model or None,
        ip_address=ip_address,
        operating_system=operating_system or None,
        environment=environment,
        location=location or None,
        status=status,
        description=description or None,
    )

    asset = asset_service.update_asset(
        db,
        asset_id,
        asset_data,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return RedirectResponse(
        url=f"/assets/{asset.id}",
        status_code=303,
    )


@router.post("/{asset_id}/delete")
def asset_delete(
    asset_id: int,
    db: Session = Depends(get_db),
):
    deleted = asset_service.delete_asset(
        db,
        asset_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return RedirectResponse(
        url="/assets",
        status_code=303,
    )
