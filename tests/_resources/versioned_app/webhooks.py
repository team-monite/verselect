from verselect import MoniteAPIRouter

router = MoniteAPIRouter(enable_internal_request_headers=False)


@router.post("/webhooks", response_model=dict)
def read_root():
    return {"saved": True}
