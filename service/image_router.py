from fastapi import UploadFile, File, HTTPException, APIRouter, Form
from fastapi.responses import JSONResponse

image_router = APIRouter()


@image_router.post("/image")
async def parse_image_endpoint(file: UploadFile = File(...)):
    try:
        raise NotImplementedError()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

