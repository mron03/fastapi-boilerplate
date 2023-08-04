import datetime
import math
from typing import Any, List, Optional
from fastapi import Depends, HTTPException, Response, status, UploadFile
from pydantic import BaseModel, Field

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from fastapi.responses import JSONResponse

from ..service import Service, get_service
from . import router
from app.utils import AppModel

import logging
import sys

logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

# Check if the handler already exists
if not logger.hasHandlers():
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.addHandler(stdout_handler)


@router.post("/", status_code=status.HTTP_200_OK)
def create_scenario(
    file: UploadFile,
    user_nickname: str = '',
    student_category: str = '',
    student_level: str = '',
    custom_filter: str = '',
    language: str = '',
    svc: Service = Depends(get_service)
):

    logger.debug(f'Sending a request to create a scenario with NICKNAME: {user_nickname}, {student_category} - student category, {student_level} - student level, {custom_filter} - custom filter')
    try:
        response = svc.repository.create_scenario(file.file, user_nickname, student_category, student_level, custom_filter, language)
    except Exception as e:
        logger.debug(e)
    return {'scenario' : response}
