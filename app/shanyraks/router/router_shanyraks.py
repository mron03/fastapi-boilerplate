import datetime
import math
from typing import Any, List, Optional
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
    price: Optional[int] = None
    address: str = ''
    area: Optional[float] = None
    rooms_count : Optional[int] = None
    description : str = ''

class CreateCommentRequest(AppModel):
    content: str = ''


#GET SHANYRAK
class GetChanyrakResponse(AppModel):
    type: str = ''
    price: Optional[int] = None
    address: str = ''
    area: Optional[float] = None
    rooms_count : Optional[int] = None
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
    price: Optional[int] = None
    address: str = ''
    area: Optional[float] = None
    rooms_count : Optional[int] = None
    description : str = ''

#GET SHANYRAKS BY FILTER
class Location(AppModel):
    latitude : str = ''
    longitude : str = ''

class Shanyrak(AppModel):
    id: Any = Field(alias="_id")
    type : str = ''
    price : Optional[int] = None
    address : str = ''
    area : Optional[float] = None
    rooms_count : Optional[int] = None
    location : Location

class GetShanyraksByFilterResponse(AppModel):
    total : int = None
    objects : List[Shanyrak]


@router.post("/", status_code=status.HTTP_200_OK)
def create_shanyrak(
    inp: CreateShanyrakResponse,
    svc: Service = Depends(get_service),
    jwt_data: JWTData = Depends(parse_jwt_user_data),
) -> dict[str, str]:
    inp = inp.dict()

    coordinates = svc.here_service.get_coordinates(inp['address'])
    inp['location'] = {'latitude' : coordinates['lat'], 'longitude' : coordinates['lng']}

    inp['created_at'] = datetime.datetime.utcnow()

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


@router.get('/', response_model=GetShanyraksByFilterResponse)
def get_shanyrak_by_filters(
    latitude : float,
    longitude : float,
    radius_in_km : float,
    limit : int = 0,
    offset : int = 0,
    type : Optional[str] = '',
    rooms_count : Optional[int] = 0,
    price_from : Optional[int] = 0,
    price_until : Optional[int] = 0,
    svc : Service = Depends(get_service),
):
    result = svc.repository.get_shanyraks_by_filter(latitude, longitude, radius_in_km, limit, offset, type, rooms_count, price_from, price_until)

    return resultcd