from pydantic import BaseModel


class Registration(BaseModel):
    email : str
    password : str

    class Config:
        from_attributes = True


class UserDetails(BaseModel):
    first_name : str | None = None
    last_name : str | None = None
    phone_number : str | None = None
    current_role : str | None = None
    specialisation : str | None = None

    class Config:
        from_attributes = True


class Login(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True