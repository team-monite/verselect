from pydantic import BaseModel

from verselect import MoniteAPIRouter

router = MoniteAPIRouter(enable_internal_request_headers=False)


class SecondVersionResponseModel(BaseModel):
    my_version2: int


@router.get("", response_model=SecondVersionResponseModel)
def read_root():
    return {"my_version2": 2}
