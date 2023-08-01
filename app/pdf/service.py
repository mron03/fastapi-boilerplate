from pydantic import BaseSettings

from app.config import database
from app.shanyraks.repository.repository_comments import CommentRepository

from .adapters.jwt_service import JwtService
from .repository.repository import PdfRepository
from .adapters.s3_service import S3Service
from .adapters.here_service import HereService

class AuthConfig(BaseSettings):
    JWT_ALG: str = "HS256"
    JWT_SECRET: str = "YOUR_SUPER_SECRET_STRING"
    JWT_EXP: int = 10_800


config = AuthConfig()

class Config(BaseSettings):
    HERE_API_KEY: str

class Service:
    def __init__(
        self,
        repository: PdfRepository,
        jwt_svc: JwtService,

    ):
    
        # config_here_service = Config()  
        self.repository = repository
        self.jwt_svc = jwt_svc
        # self.s3_service = S3Service()
        # self.here_service = HereService(config_here_service.HERE_API_KEY)


def get_service():
    repository = PdfRepository(database)
    jwt_svc = JwtService(config.JWT_ALG, config.JWT_SECRET, config.JWT_EXP)

    svc = Service(repository, jwt_svc)
    return svc
