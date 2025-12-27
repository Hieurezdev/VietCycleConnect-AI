from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def ok() -> dict[str, str]:
    return {"status": "ok"}
