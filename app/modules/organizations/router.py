from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import pagination_params
from app.core.permissions import require_role
from app.modules.users.repository import UserRepository

from .repository import OrganizationRepository
from .schemas import OrganizationCreate, OrganizationUpdate
from .service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_service(db=Depends(get_db)):
    return OrganizationService(
        OrganizationRepository(db),
        UserRepository(db)
    )


@router.get("/dashboard/summary")
async def get_org_summary(
    user=Depends(get_current_user),
    s=Depends(get_service)
):
    """
    Personalized Dashboard Summary.
    Returns global stats for admins and personal performance for clinical staff.
    """
    return await s.repo.get_summary_stats(
        org_id=user["org"],
        role=user["role"],
        user_id=user["sub"]
    )

@router.get("/diag/context")
async def debug_context(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Diagnostic: Check token vs database state."""
    # 1. Check if user exists in DB
    r = await db.execute(
        text("SELECT id, email, role, organization_id, active FROM users WHERE id = CAST(:id AS UUID)"),
        {"id": user["sub"]}
    )
    db_user = r.mappings().first()

    # 2. Check encounters for this user
    e = await db.execute(
        text("SELECT COUNT(*) as count FROM encounters WHERE doctor_id = CAST(:id AS UUID)"),
        {"id": user["sub"]}
    )
    encounters_count = e.mappings().first()

    return {
        "token_context": user,
        "db_user_record": db_user,
        "raw_encounters_count": encounters_count["count"] if encounters_count else 0
    }

@router.post("")
async def create_org(
    payload: OrganizationCreate, 
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """
    Manual creation of organizations.
    SaaS Guard: Only Super Admins (no linked org or special global org) should do this.
    For self-service, use /auth/register-saas.
    """
    # Logic to identify if it's the global admin (e.g., email or special org name)
    if user.get("email") != "mdiazcabr@gmail.com":
        raise HTTPException(status_code=403, detail="Only global administrators can create organizations manually.")
        
    return await s.create(payload, user["sub"])


@router.get("")
async def list_orgs(
    page=Depends(pagination_params), 
    user=Depends(get_current_user),
    s=Depends(get_service)
):
    """
    List organizations.
    SaaS Guard: Normal admins only see their own. Super admin sees all.
    """
    if user.get("email") == "mdiazcabr@gmail.com":
        return await s.list(page.limit, page.offset)
    
    # Filter for normal user
    org_id = user.get("org")
    if not org_id:
        return []
    return [await s.get(org_id)]


@router.get("/{org_id}")
async def get_org(
    org_id: str, 
    user=Depends(get_current_user),
    s=Depends(get_service)
):
    """Secure fetch: Only your own org unless superadmin."""
    if user.get("email") != "mdiazcabr@gmail.com" and str(user.get("org")) != org_id:
        raise HTTPException(status_code=403, detail="Access denied to this organization.")
        
    return await s.get(org_id)


@router.put("/{org_id}")
async def update_org(
    org_id: str,
    payload: OrganizationUpdate,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    """Secure update: Only your own org unless superadmin."""
    if user.get("email") != "mdiazcabr@gmail.com" and str(user.get("org")) != org_id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    return await s.update(org_id, payload)


@router.patch("/{org_id}/deactivate")
async def deactivate_org(
    org_id: str, 
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """SaaS Guard: Only global admin can deactivate entire organizations."""
    if user.get("email") != "mdiazcabr@gmail.com":
        raise HTTPException(status_code=403, detail="Only global admins can deactivate organizations.")
        
    await s.deactivate(org_id)
    return {"status": "deactivated"}


@router.patch("/{org_id}/activate")
async def activate_org(
    org_id: str, 
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """SaaS Guard: Only global admin can re-activate organizations."""
    if user.get("email") != "mdiazcabr@gmail.com":
        raise HTTPException(status_code=403, detail="Only global admins can activate organizations.")
        
    await s.activate(org_id)
    return {"status": "activated"}
