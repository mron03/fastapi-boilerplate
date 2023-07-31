from fastapi import Depends, Response, status, UploadFile
from pydantic import Field
from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from typing import Any
from app.utils import AppModel

from ..service import Service, get_service
from . import router


@router.post('/users/avatar')
def upload_avatar(
    avatar : UploadFile,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
):
    # url = svc.s3_service.upload_file(avatar.file, avatar.filename)

    update = svc.repository.upload_avatar(jwd_data.user_id, avatar.filename)
    
    if update.modified_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)

@router.delete('/users/avatar')
def delete_avatar(
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    # avatar_url = svc.repository.get_avatar_url(jwd_data.user_id)
    # svc.s3_service.delete_file(avatar_url)
    update = svc.repository.delete_avatar(jwd_data.user_id)

    if update.modified_count == 1:
        return Response(status_code=200)
    
    return Response(status_code=404)