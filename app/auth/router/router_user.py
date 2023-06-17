from typing import Any
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import Field
from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data

from app.utils import AppModel

from ..service import Service, get_service
from ..utils.security import check_password
from . import router
from .errors import InvalidCredentialsException

#AUTHORIZE ACCOUNT
class AuthorizeUserResponse(AppModel):
    access_token: str
    token_type: str = "Bearer"

#GET ACCOUNT
class GetMyAccountResponse(AppModel):
    id: Any = Field(alias="_id")
    email: str = ''
    phone : str = ''
    name : str = ''
    city : str = ''
    avatar_url : str = ''

#REGISTER ACCOUNT
class RegisterUserRequest(AppModel):
    email: str
    password: str

class RegisterUserResponse(AppModel):
    email: str

#UPDATE ACCOUNT INFO
class UpdateUserResponse(AppModel):
    phone : str
    name : str
    city : str



@router.post("/users/tokens", response_model=AuthorizeUserResponse)
def authorize_user(
    input: OAuth2PasswordRequestForm = Depends(),
    svc: Service = Depends(get_service),
) -> AuthorizeUserResponse:
    user = svc.repository.get_user_by_email(input.username)

    if not user:
        raise InvalidCredentialsException

    if not check_password(input.password, user["password"]):
        raise InvalidCredentialsException

    return AuthorizeUserResponse(
        access_token=svc.jwt_svc.create_access_token(user=user),
    )



@router.get("/users/me", response_model=GetMyAccountResponse)
def get_my_account(
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> dict[str, str]:
    user = svc.repository.get_user_by_id(jwt_data.user_id)
    return user



@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=RegisterUserResponse)
def register_user(
    input: RegisterUserRequest,
    svc: Service = Depends(get_service),
) -> dict[str, str]:
    if svc.repository.get_user_by_email(input.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already taken.",
        )

    svc.repository.create_user(input.dict())

    return RegisterUserResponse(email=input.email)


@router.patch("/users/me")
def update_user(
    input : UpdateUserResponse,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> dict[str, str]:
    
    svc.repository.update_user(jwt_data.user_id, input.dict())
    return Response(status_code=200)
