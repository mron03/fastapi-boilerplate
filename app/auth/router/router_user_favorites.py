from fastapi import Depends, Response, status
from pydantic import Field
from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from typing import Any
from app.utils import AppModel

from ..service import Service, get_service
from . import router


class UserFavoriteShanyraksResponse(AppModel):
    id : Any = Field(alias = '_id')
    address : str

class Favorites(AppModel):
    favorites : list[UserFavoriteShanyraksResponse]


@router.post("/users/favorites/shanyraks/{shanyrak_id : str}")
def add_shanyrak_to_favorites(
    shanyrak_id : str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Response:
    
    update = svc.repository.add_shanyrak_to_favorites(shanyrak_id, jwt_data.user_id)
    
    return Response(status_code=200)


@router.get("/users/favorites/shanyraks", status_code=status.HTTP_200_OK, response_model=Favorites)
def get_favorite_shanyraks(
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> UserFavoriteShanyraksResponse:
    shanyraks = svc.repository.get_shanyraks_by_ids(jwt_data.user_id)
    return Favorites(favorites = shanyraks)
 

@router.delete("/users/favorites/shanyraks/{shanyrak_id : str}")
def delete_favorite_shanyrak(
    shanyrak_id : str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
):
    update = svc.repository.delete_favorite_shanyrak_by_id(jwt_data.user_id, shanyrak_id)

    if update.modified_count == 1:
        return Response(status_code=200)
    
    return Response(status_code=404)