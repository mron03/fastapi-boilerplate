from fastapi import Depends, Response, UploadFile
from typing import List
from ..adapters.jwt_service import JWTData, JwtService
from .dependencies import parse_jwt_user_data
from ..service import Service, get_service
from . import router
from app.utils import AppModel


@router.post("/{shanyrak_id : str}/media")
def upload_files(
    files: List[UploadFile],
    shanyrak_id : str,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
):
    
    result = []
    for file in files:
        url = svc.s3_service.upload_file(file.file, file.filename)

        result.append(url)
    
    
    update = svc.repository.upload_files(shanyrak_id, jwd_data.user_id, result)

    if update.modified_count == 1: 
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