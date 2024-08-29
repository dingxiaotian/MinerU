import os, sys
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse

import tempfile
import shutil
import subprocess

# 单独debug时启用
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from api_service.utils import b64_decode, download_document, pdf_parse_main
from magic_doc.docconv import DocConverter

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
    parse_method = req_info.get('parse_method', 'auto')

    if not len(url) and not len(doc_b64):
        res_dict['message'] = 'Both document url and document base64 data are empty.'
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
    # Create a temp dir.
    temp_dir = tempfile.mkdtemp()
    try:
        success, msg, res = pdf_parse_main(pdf_bytes=file_bytes,
                                                parse_method=parse_method,
                                                out_img_path=temp_dir
                                                )
        res_dict['success'] = success
        res_dict['message'] = msg
        res_dict['data'] = res
    
    except Exception as e:
        print(e)
        res_dict['success'] = False
        res_dict['message'] = str(e)

    finally:
        # 清除临时文件夹及其内容
        shutil.rmtree(temp_dir)
        return JSONResponse(content=res_dict, media_type='application/json')

@document_router.post("/pdfdocs")
async def parse_any_endpoint(info: Request):
    '''非PDF文档转换为PDF文档再处理
    '''
    req_info = await info.json()
    # Init responds dict.
    res_dict = {}
    res_dict['success'] = False
    res_dict['message'] = ''
    res_dict['data'] = {}

    url = req_info.get('url', '')
    doc_b64 = req_info.get('base64', '')
    parse_method = req_info.get('parse_method', 'auto')
    file_name = req_info.get('file_name', '')

    if not len(url) and not len(doc_b64):
        res_dict['message'] = 'Both document url and document base64 data are empty.'
        return JSONResponse(content=res_dict, media_type='application/json')
    
    if not len(file_name):
        res_dict['message'] = 'File name are empty.'
        return JSONResponse(content=res_dict, media_type='application/json')

    allowed_extensions = {".pdf", ".ppt", ".pptx", ".doc", ".docx"}
    file_ext = os.path.splitext(file_name)[1]

    if file_ext.lower() not in allowed_extensions:
        res_dict['message'] = "Unsupported file type. Only PDF, PPT, and DOCX are allowed."
        return JSONResponse(content=res_dict, media_type='application/json')

    # if has document b64:
    file_bytes = b''
    if len(doc_b64):
        file_bytes = b64_decode(doc_b64)

    if not len(file_bytes) and len(url):
        file_bytes = download_document(url)

    # 创建临时ppt文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as tmp_file:
        tmp_file.write(file_bytes)
        tmp_file.flush()
        input_path = tmp_file.name

    output_dir = tempfile.mkdtemp()
    command = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        input_path,
    ]

    try:
        result = subprocess.run(command, check=True)
        print(f"PDF conversion executed with return code: {result.returncode}")
    except subprocess.CalledProcessError as e:
        msg = f"PDF conversion failed with return code: {e.returncode}"
        res_dict['message'] = msg
        return JSONResponse(content=res_dict, media_type='application/json')

    output_pdf = os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")

    with open(output_pdf, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    try:
        success, msg, res = pdf_parse_main(pdf_bytes=pdf_bytes,
                                                parse_method=parse_method,
                                                out_img_path=output_dir
                                                )
        res_dict['success'] = success
        res_dict['message'] = msg
        res_dict['data'] = res
    
    except Exception as e:
        print(e)
        res_dict['success'] = False
        res_dict['message'] = str(e)

    finally:
        # 清除临时文件夹及其内容
        os.remove(input_path)
        os.remove(output_pdf)
        shutil.rmtree(output_dir)
        return JSONResponse(content=res_dict, media_type='application/json')
    

@document_router.post("/docs")
async def parse_office_endpoint(info: Request):
    '''解析Office文档
    '''
    req_info = await info.json()
    # Init responds dict.
    res_dict = {}
    res_dict['success'] = False
    res_dict['message'] = ''
    res_dict['data'] = {}

    url = req_info.get('url', '')
    doc_b64 = req_info.get('base64', '')
    parse_method = req_info.get('parse_method', 'auto')  # unused
    file_name = req_info.get('file_name', '')

    if not len(url) and not len(doc_b64):
        res_dict['message'] = 'Both document url and document base64 data are empty.'
        return JSONResponse(content=res_dict, media_type='application/json')
    
    if not len(file_name):
        res_dict['message'] = 'File name are empty.'
        return JSONResponse(content=res_dict, media_type='application/json')

    allowed_extensions = {".ppt", ".pptx", ".doc", ".docx"}
    file_ext = os.path.splitext(file_name)[1]

    if file_ext.lower() not in allowed_extensions:
        res_dict['message'] = "Unsupported file type. Only MS Office ppt, pptx, doc, and docx are allowed."
        return JSONResponse(content=res_dict, media_type='application/json')

    # if has document b64:
    file_bytes = b''
    if len(doc_b64):
        file_bytes = b64_decode(doc_b64)

    if not len(file_bytes) and len(url):
        file_bytes = download_document(url)

    # 创建临时ppt文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as tmp_file:
        tmp_file.write(file_bytes)
        tmp_file.flush()
        input_path = tmp_file.name

    converter = DocConverter(s3_config=None)
    try:
        markdown_content, time_cost = converter.convert(input_path, conv_timeout=300)
        res_dict['success'] = True
        res_dict['message'] = 'success'
        res_dict['data'] = {
                    'markdown': markdown_content,
                    'json': ''
        }
    
    except Exception as e:
        print(e)
        res_dict['success'] = False
        res_dict['message'] = str(e)

    finally:
        # 清除临时文件夹及其内容
        os.remove(input_path)
        return JSONResponse(content=res_dict, media_type='application/json')