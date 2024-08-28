from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse

website_router = APIRouter()


# Website parsing endpoint
@website_router.post("/parse")
async def parse_website(url: str):
    try:
        raise NotImplementedError()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@website_router.post("/crawl")
async def crawl_website(url: str):
    return {"Coming soon"}


@website_router.post("/search")
async def search_web(url: str, prompt: str):
    return {"Coming soon"}
