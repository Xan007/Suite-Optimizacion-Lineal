from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/")
def test() -> dict:
    return {"message": "Test done"}


@router.get("/health-check/")
async def health_check() -> bool:
    return True