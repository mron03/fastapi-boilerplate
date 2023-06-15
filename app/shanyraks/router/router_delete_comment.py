from fastapi import Depends, FastAPI, Response
from app.utils import AppModel
from ..service import Service, get_service
from . import router
from ..adapters.jwt_service import JWTData, JwtService
from .dependencies import parse_jwt_user_data


@router.delete('/{shanyrak_id : str}/comment/{comment_id : str}')
def delete_comment(
    shanyrak_id : str,
    comment_id : str,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    delete = svc.comment_repository.delete_comment_by_id(comment_id, jwd_data.user_id)

    if delete.deleted_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)