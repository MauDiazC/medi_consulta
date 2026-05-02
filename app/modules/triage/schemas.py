from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class TriageBase(BaseModel):
    patient_id: UUID
    appointment_id: UUID | None = None
    heart_rate: float | None = None
    oxygen_saturation: float | None = None
    blood_pressure: str | None = None
    weight: float | None = None
    height: float | None = None
    temperature: float | None = None

class TriageCreate(TriageBase):
    pass

class TriageRead(TriageBase):
    id: UUID
    doctor_id: UUID
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def vital_signs_taken(self) -> bool:
        """
        Determina si se han tomado signos vitales basándose en si al menos uno está presente.
        """
        return any([
            self.heart_rate is not None,
            self.oxygen_saturation is not None,
            self.blood_pressure is not None,
            self.weight is not None,
            self.height is not None,
            self.temperature is not None
        ])
