from fastapi import Depends, Response
from app.utils import AppModel
from ..service import Service, get_service
from . import router
from ..adapters.jwt_service import JWTData
from .dependencies import parse_jwt_user_data



class UpdateUserResponse(AppModel):
    phone : str
    name : str
    city : str


@router.patch(
    "/users/me"
)
def update_user(
    input : UpdateUserResponse,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> dict[str, str]:
    
    svc.repository.update_user(jwt_data.user_id, input.dict())
    return Response(status_code=200)
