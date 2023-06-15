from fastapi import Depends, FastAPI, Response
from app.utils import AppModel
from ..service import Service, get_service
from . import router
from ..adapters.jwt_service import JWTData, JwtService
from .dependencies import parse_jwt_user_data


class UpdateShanyrakRequest(AppModel):
    type: str = ''
    price: str = ''
    address: str = ''
    area: str = ''
    rooms_count : str = ''
    description : str = ''


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


@router.delete('/{shanyrak_id : str}/media')
def delete_files(
    shanyrak_id : str,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    
    shanyrak = svc.repository.get_shanyrak_by_id(shanyrak_id)
    media_files = shanyrak.get('media' , [])

    for media_file in media_files:
        svc.s3_service.delete_file(media_file)
    
    update_shanyrak = svc.repository.update_shanyrak(shanyrak_id, jwd_data.user_id, {'media' : []})

    if update_shanyrak.modified_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)