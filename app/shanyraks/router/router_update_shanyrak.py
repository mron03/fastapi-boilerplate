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


@router.patch('/{sh_id : str}')
def update_shanyrak(
    sh_id : str,
    inp : UpdateShanyrakRequest,
    jwd_data : JWTData = Depends(parse_jwt_user_data),
    svc : Service = Depends(get_service),
):
    update = svc.repository.update_shanyrak(sh_id, jwd_data.user_id, inp.dict())

    if update.modified_count == 1: 
        return Response(status_code=200)

    return Response(status_code=400)

