from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def v1_root() -> dict[str, str]:
    return {"message": "API v1"}
