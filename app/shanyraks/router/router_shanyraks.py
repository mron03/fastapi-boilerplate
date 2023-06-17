import datetime
from typing import Any, List
from fastapi import Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

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


#GET SHANYRAK
class GetChanyrakResponse(AppModel):
    type: str = ''
    price: str = ''
    address: str = ''
    area: str = ''
    rooms_count : str = ''
    description : str = ''
    media : List = None
    location : dict = None

class GetCommentResponse(AppModel):
    id: Any = Field(alias="_id")
    content: str
    created_at: str
    author_id: str

#UPDATE SHANYRAK
class UpdateShanyrakRequest(AppModel):
    type: str = ''
    price: str = ''
    address: str = ''
    area: str = ''
    rooms_count : str = ''
    description : str = ''



@router.post("/", status_code=status.HTTP_200_OK)
def create_shanyrak(
    inp: CreateShanyrakResponse,
    svc: Service = Depends(get_service),
    jwt_data: JWTData = Depends(parse_jwt_user_data),
) -> dict[str, str]:
    inp = inp.dict()
    inp['location'] = svc.here_service.get_coordinates(inp['address'])
    response = svc.repository.create_shanyrak(jwt_data.user_id, inp)

    return {'id' : str(response.inserted_id)}


@router.get('/{shanyrak_id : str}', response_model=GetChanyrakResponse)
def get_shanyrak(
    shanyrak_id : str,
    svc: Service = Depends(get_service),
    jwt_data: JWTData = Depends(parse_jwt_user_data),
) -> dict[str, str]:
    shanyrak = svc.repository.get_shanyrak_by_id(shanyrak_id)

    return shanyrak

@router.patch('/{shanyrak_id : str}')
def update_shanyrak(
    shanyrak_id : str,
    inp : UpdateShanyrakRequest,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    update = svc.repository.update_shanyrak(shanyrak_id, jwd_data.user_id, inp.dict())

    if update.modified_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)


@router.delete('/{shanyrak_id : str}')
def delete_shanyrak(
    shanyrak_id : str,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    delete = svc.repository.delete_shanyrak(shanyrak_id, jwd_data.user_id)

    if delete.deleted_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)