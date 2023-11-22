from pydantic import BaseModel

from fastapi.routing import APIRouter

router = APIRouter(prefix="/v1")


class SecondVersionResponseModel(BaseModel):
    my_version2: int


@router.get("", response_model=SecondVersionResponseModel)
def read_root():
    return {"my_version2": 2}
