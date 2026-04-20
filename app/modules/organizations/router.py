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
    start_date: str | None = None,
    end_date: str | None = None,
    user=Depends(get_current_user),
    s=Depends(get_service)
):
    """
    Personalized Dashboard Summary.
    Returns global stats for admins and personal performance for clinical staff.
    """
    return await s.get_summary_stats(
        org_id=user["org"],
        role=user["role"],
        user_id=user["sub"],
        start_date=start_date,
        end_date=end_date
    )

@router.get("/diag/context")
async def debug_context(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Diagnostic: Deep dive into DB state and identities."""
    # 1. User check (current logged in user)
    r = await db.execute(
        text("SELECT id, email, role, organization_id, active FROM users WHERE id = CAST(:id AS UUID)"),
        {"id": user["sub"]}
    )
    db_user = r.mappings().first()

    # 2. Identities Audit (Check specifically for the IDs in question)
    ids_to_audit = [
        'eb1fcdad-8823-4690-b4b4-14948c6fcf95',
        '009ea9b5-bc19-4a12-9417-7285d76d8174',
        user["sub"]
    ]
    audit_r = await db.execute(
        text("SELECT id, email, role, organization_id FROM users WHERE id IN (SELECT CAST(id AS UUID) FROM (VALUES (:id1), (:id2), (:id3)) as t(id))"),
        {"id1": ids_to_audit[0], "id2": ids_to_audit[1], "id3": ids_to_audit[2]}
    )
    identities = audit_r.mappings().all()

    # 3. Encounters for THIS user
    e_user = await db.execute(
        text("SELECT id, organization_id, doctor_id, status, created_at FROM encounters WHERE doctor_id = CAST(:id AS UUID)"),
        {"id": user["sub"]}
    )
    my_encounters = e_user.mappings().all()

    # 4. GLOBAL Encounter Check (Are there ANY encounters at all?)
    e_global = await db.execute(text("SELECT id, doctor_id, organization_id, status FROM encounters LIMIT 5"))
    any_encounters = e_global.mappings().all()

    # 5. Patient Check
    p_check = await db.execute(text("SELECT COUNT(*) as count FROM patients WHERE organization_id = CAST(:oid AS UUID)"), {"oid": user["org"]})
    patient_count = p_check.mappings().first()

    # 6. Org Check
    o = await db.execute(
        text("SELECT id, name FROM organizations WHERE id = CAST(:id AS UUID)"),
        {"id": user["org"]}
    )
    org_record = o.mappings().first()

    return {
        "token_context": user,
        "db_user_record": db_user,
        "org_record": org_record,
        "identities_audit": [
            {
                "id": str(ident["id"]),
                "email": ident["email"],
                "role": ident["role"],
                "org_id": str(ident["organization_id"])
            }
            for ident in identities
        ],
        "my_encounters_count": len(my_encounters),
        "my_encounters": [
            {
                "id": str(enc["id"]),
                "doctor_id": str(enc["doctor_id"]),
                "organization_id": str(enc["organization_id"]),
                "status": enc["status"]
            }
            for enc in my_encounters
        ],
        "global_system_encounters": [
            {
                "id": str(enc["id"]),
                "doctor_id": str(enc["doctor_id"]),
                "org_id": str(enc["organization_id"]),
                "status": enc["status"]
            }
            for enc in any_encounters
        ],
        "organization_patient_count": patient_count["count"] if patient_count else 0
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
