from typing import Any, List
from fastapi import Depends, HTTPException, Response
from pydantic import Field

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data

from ..service import Service, get_service
from . import router
from ...utils import AppModel


class CreateCommentRequest(AppModel):
    content: str

#GET COMMENTS
class GetCommentResponse(AppModel):
    id: Any = Field(alias="_id")
    content: str
    created_at: str
    author_id: str

#UPDATE COMMENTS
class UpdateCommentRequest(AppModel):
    content : str = ''


# ==========================================
# ==========================================

@router.post("/{shanyrak_id:str}/comments")
def create_comment(
    shanyrak_id: str,
    request: CreateCommentRequest,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Response:
    user_id = jwt_data.user_id
    success = svc.comment_repository.create_comment(shanyrak_id=shanyrak_id, user_id=user_id, payload=request.dict())
    if not success:
        raise HTTPException(status_code=404, detail=f"Could not insert")
    return Response(status_code=200)


@router.get("/{shanyrak_id:str}/comments", response_model=List[GetCommentResponse])
def get_comment(
        shanyrak_id: str,
        jwt_data: JWTData = Depends(parse_jwt_user_data),
        svc: Service = Depends(get_service),
) -> List[GetCommentResponse]:
    comments = svc.comment_repository.get_comments_by_shanyrak_id(shanyrak_id=shanyrak_id)
    return [GetCommentResponse(**comment) for comment in comments]


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