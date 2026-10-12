from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field("student", pattern="^(student|counsellor|admin)$")
    department: Optional[str] = "Computer Science"
    academic_year: Optional[str] = "3rd Year"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    user_ref: Optional[str]
    email: str
    full_name: str
    role: str
    department: Optional[str]
    academic_year: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
