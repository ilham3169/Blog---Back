from fastapi import APIRouter

router = APIRouter(
    prefix="/test",
    tags=["test"]
)

@router.post("/")
async def login_for_access_token():
    return "This is the test endpoint for now"
