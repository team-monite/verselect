from verselect import MoniteAPIRouter

from .create_schemas import MySchema as CreateSchema
from .update_schemas import MySchema as UpdateSchema

router = MoniteAPIRouter(enable_internal_request_headers=False)


@router.post("/companies", responses={201: {"model": CreateSchema}})
def create_companies(payload: CreateSchema):
    raise NotImplementedError


@router.patch("/companies")
def update_companies(payload: UpdateSchema):
    raise NotImplementedError
