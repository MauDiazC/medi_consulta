from pydantic import BaseModel


class PatientCreate(BaseModel):
    first_name: str
    last_name: str


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None