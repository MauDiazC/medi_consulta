from fastapi import HTTPException, status

from app.core.security import (create_access_token, verify_password, 
                               verify_supabase_token, normalize_supabase_identity)

from .repository import AuthRepository


class AuthService:

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def login(self, email: str, password: str):

        user = await self.repo.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not verify_password(
            password,
            user["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Preserve null if organization_id is missing (Bootstrap case)
        org_id = str(user["organization_id"]) if user["organization_id"] else None

        token = create_access_token(
            {
                "sub": str(user["id"]),
                "org": org_id,
                "role": user["role"],
            }
        )

        return token

    async def exchange(self, supabase_token: str):
        """
        Hardened Token Exchange Flow.
        Bridges Supabase Identity Provider with Mediconsulta Authorization.
        """
        # 1. Forensic Identity Verification
        try:
            claims = await verify_supabase_token(supabase_token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Identity verification failed: {str(e)}"
            )

        # 2. Domain Mapping (sub -> users.id)
        user_id = claims.get("sub")
        user = await self.repo.get_user_by_id(user_id)

        if not user:
            # Identity is valid, but no corresponding domain record exists.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User identity verified but not onboarded in Mediconsulta."
            )

        # 3. Contextual Domain Token Issuance
        org_id = str(user["organization_id"]) if user["organization_id"] else None

        return create_access_token(
            {
                "sub": str(user["id"]),
                "org": org_id,
                "role": user["role"],
            }
        )

    async def bootstrap(self, supabase_token: str):
        """
        Hardened Onboarding Bootstrap.
        Allows verified external identities to provision their domain presence.
        """
        # 1. Forensic Verification
        try:
            claims = await verify_supabase_token(supabase_token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Identity verification failed: {str(e)}"
            )

        # 2. Normalization (Boundary: Service remains agnostic of claim formatting)
        identity = normalize_supabase_identity(claims)

        # 3. State Resolution
        user = await self.repo.get_user_by_id(identity["id"])

        if not user:
            # 4. Genesis Provisioning (Executes within request-scoped transaction)
            user = await self.repo.bootstrap_user(
                user_id=identity["id"],
                email=identity["email"],
                full_name=identity["full_name"],
                role="admin"  # First user defaults to institutional admin
            )

        # 5. Issue Token (organization_id is naturally None here)
        org_id = str(user["organization_id"]) if user["organization_id"] else None
        
        return create_access_token({
            "sub": str(user["id"]),
            "org": org_id,
            "role": user["role"]
        })
