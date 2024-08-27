from fastapi import UploadFile, File, HTTPException, APIRouter, Form
from fastapi.responses import JSONResponse

image_router = APIRouter()


@image_router.post("/image")
async def parse_image_endpoint(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        result: responseDocument = parse_image(file_bytes, model_state)
        return JSONResponse(content=result.model_dump())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@image_router.post("/process_image")
async def process_image_route(image: UploadFile = File(...), task: str = Form(...)):
    try:
        file_bytes = await image.read()
        result: responseDocument = process_image(file_bytes, task, model_state)
        return JSONResponse(content=result.model_dump())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
