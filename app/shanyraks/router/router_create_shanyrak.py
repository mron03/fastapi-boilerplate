import datetime
from fastapi import Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from fastapi.responses import JSONResponse

from ..service import Service, get_service
from . import router
from app.utils import AppModel

class CreateShanyrakResponse(AppModel):
    type: str = ''
    price: str = ''
    address: str = ''
    area: str = ''
    rooms_count : str = ''
    description : str = ''

class CreateCommentRequest(AppModel):
    content: str = ''

@router.post(
    "/", status_code=status.HTTP_200_OK
)
def create_shanyrak(
    inp: CreateShanyrakResponse,
    svc: Service = Depends(get_service),
    jwt_data: JWTData = Depends(parse_jwt_user_data),
) -> dict[str, str]:
    inp = inp.dict()
    inp['location'] = svc.here_service.get_coordinates(inp['address'])
    response = svc.repository.create_shanyrak(jwt_data.user_id, inp)

    return {'id' : str(response.inserted_id)}