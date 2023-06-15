from pydantic import Field
from typing import Any, List
from fastapi import Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from fastapi.responses import JSONResponse

from ..service import Service, get_service
from . import router
from app.utils import AppModel

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

@router.get('/{shanyrak_id : str}', response_model=GetChanyrakResponse)
def get_shanyrak(
    shanyrak_id : str,
    svc: Service = Depends(get_service),
    jwt_data: JWTData = Depends(parse_jwt_user_data),
) -> dict[str, str]:
    shanyrak = svc.repository.get_shanyrak_by_id(shanyrak_id)

    return shanyrak
