from fastapi import Depends, FastAPI, Response
from app.utils import AppModel
from ..service import Service, get_service
from . import router
from ..adapters.jwt_service import JWTData, JwtService
from .dependencies import parse_jwt_user_data


class UpdateCommentRequest(AppModel):
    content : str = ''


@router.patch('/{shanyrak_id : str}/comments/{comment_id : str}')
def update_comment(
    shanyrak_id : str,
    comment_id : str,
    inp : UpdateCommentRequest,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    update = svc.comment_repository.update_comment_by_id(comment_id, jwd_data.user_id, inp.dict())

    if update.modified_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)