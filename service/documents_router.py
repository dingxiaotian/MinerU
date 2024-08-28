import os, sys
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse

# 单独debug时启用
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from service.utils import b64_decode, download_document

# Document parsing router.
document_router = APIRouter()

# Document parsing endpoints
@document_router.post("/pdf")
async def parse_pdf_endpoint(info: Request):
    req_info = await info.json()

    # Init responds dict.
    res_dict = {}
    res_dict['success'] = False
    res_dict['message'] = ''
    res_dict['data'] = {}

    url = req_info.get('url', '')
    doc_b64 = req_info.get('base64', '')

    if not len(url) and not len(doc_b64):
        res_dict['message'] = 'Both pdf url and document base64 data are empty.'
        return JSONResponse(content=res_dict, media_type='application/json')

    # if has document b64:
    file_bytes = b''
    if len(doc_b64):
        file_bytes = b64_decode(doc_b64)

    if not len(file_bytes) and len(url):
        file_bytes = download_document(url)

    # 如果最终没有filebytes
    if not(file_bytes):
        res_dict['message'] = 'Cannot get file data.'
        return JSONResponse(content=res_dict, media_type='application/json')
    
    # Start processing.
    try:
        full_text, images, out_meta = convert_single_pdf(
            file_bytes, model_state.model_list
        )

        result = responseDocument(text=full_text, metadata=out_meta)
        encode_images(images, result)
        # result : responseDocument = convert_single_pdf(file_bytes , model_state.model_list)

        return JSONResponse(content=result.model_dump())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Document parsing endpoints
@document_router.post("/ppt")
async def parse_ppt_endpoint(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ppt") as tmp_ppt:
        tmp_ppt.write(await file.read())
        tmp_ppt.flush()
        input_path = tmp_ppt.name

    output_dir = tempfile.mkdtemp()
    command = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        input_path,
    ]
    subprocess.run(command, check=True)

    output_pdf_path = os.path.join(
        output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
    )

    with open(output_pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    full_text, images, out_meta = convert_single_pdf(pdf_bytes, model_state.model_list)

    os.remove(input_path)
    os.remove(output_pdf_path)
    os.rmdir(output_dir)

    result = responseDocument(text=full_text, metadata=out_meta)
    encode_images(images, result)

    return JSONResponse(content=result.model_dump())


@document_router.post("/docs")
async def parse_doc_endpoint(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ppt") as tmp_ppt:
        tmp_ppt.write(await file.read())
        tmp_ppt.flush()
        input_path = tmp_ppt.name

    output_dir = tempfile.mkdtemp()
    command = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        input_path,
    ]
    subprocess.run(command, check=True)

    output_pdf_path = os.path.join(
        output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
    )

    with open(output_pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    full_text, images, out_meta = convert_single_pdf(pdf_bytes, model_state.model_list)

    result = responseDocument(text=full_text, metadata=out_meta)
    encode_images(images, result)

    return JSONResponse(content=result.model_dump())


@document_router.post("")
async def parse_any_endpoint(file: UploadFile = File(...)):
    allowed_extensions = {".pdf", ".ppt", ".pptx", ".doc", ".docx"}
    file_ext = os.path.splitext(file.filename)[1]

    if file_ext.lower() not in allowed_extensions:
        return JSONResponse(
            content={
                "message": "Unsupported file type. Only PDF, PPT, and DOCX are allowed."
            },
            status_code=400,
        )

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(await file.read())
        tmp_file.flush()
        input_path = tmp_file.name

    if file_ext.lower() in {".ppt", ".pptx", ".doc", ".docx"}:
        output_dir = tempfile.mkdtemp()
        command = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            input_path,
        ]
        subprocess.run(command, check=True)
        output_pdf_path = os.path.join(
            output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        )
        input_path = output_pdf_path

    # Common parsing logic
    full_text, images, out_meta = convert_single_pdf(input_path, model_state.model_list)

    os.remove(input_path)

    result = responseDocument(text=full_text, metadata=out_meta)
    encode_images(images, result)

    return JSONResponse(content=result.model_dump())


# @document_router.post("/docs")
# async def parse_docs_endpoint(file: UploadFile = File(...)):
#     try:

#         file_bytes = await file.read()
#         result = parse_doc(file_bytes , model_state)

#         return JSONResponse(content=result)

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @document_router.post("/ppt")
# async def parse_ppt_endpoint(file: UploadFile = File(...)):
#     try:
#         file_bytes = await file.read()
#         result = parse_ppt(file_bytes , model_state)

#         return JSONResponse(content=result)

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))