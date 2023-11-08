from pydantic import BaseModel


class ResponseModel(BaseModel):
    my_version2: int
