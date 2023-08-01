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
from typing import List

import logging
import sys

logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(stdout_handler)

class CreateScenarioRequest(AppModel):
    youtube_urls : List[str] = []
    youtube_prompt: str = ''
    student_category: str = ''
    student_level: str = ''
    custom_filter: str = ''

@router.post("/create-scenario", status_code=status.HTTP_200_OK)
def create_scenario(
    inp: CreateScenarioRequest,
    svc: Service = Depends(get_service)
):
    
    youtube_urls = inp.youtube_urls
    youtube_prompt = inp.youtube_prompt
    student_category = inp.student_category
    student_level = inp.student_level
    custom_filter = inp.custom_filter

    logger.debug(f'Sending a request to create a scenario with YOUTUBE URLS: {youtube_urls}, YOUTUBE PROMPT: {youtube_prompt}  STUDENT CATEGORY: {student_category} STUDENT LEVEL: {student_level} CUSTOM FILTER: {custom_filter}')
    response = svc.repository.create_scenario_with_youtube(youtube_urls, youtube_prompt, student_category, student_level, custom_filter)
    return {'scenario' : response}
