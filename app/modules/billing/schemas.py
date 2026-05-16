from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class CheckoutRequest(BaseModel):
    plan_code: str  # plan_medico, plan_consultorio, plan_clinica_premium

class CheckoutResponse(BaseModel):
    checkout_url: str

class InvoiceRequest(BaseModel):
    rfc: str
    legal_name: str
    tax_system: str
    zip_code: str
    use: str = "G03"  # Gastos en general

class PaymentDTO(BaseModel):
    id: UUID
    organization_id: UUID
    amount: float
    currency: str
    status: str
    cfdi_status: str
    created_at: datetime

class CFDIRead(BaseModel):
    id: UUID
    payment_id: UUID
    uuid_sat: Optional[str]
    xml_url: Optional[str]
    pdf_url: Optional[str]
    status: str
    created_at: datetime
