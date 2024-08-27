# -*- coding: utf-8 -*-

import os, sys
import time
import asyncio

import logging
from datetime import datetime, date

from typing import Optional
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request, APIRouter, Depends
import json

from fastapi.responses import JSONResponse
from service.auth import authenticated

logger = logging.getLogger(__name__)

# initialize Fastapi application.
app = FastAPI()

@app.api_route("/Generate/Mindmap", methods=["post"], dependencies=[Depends(authenticated)])
async def generate_mindmap(info: Request):
    """
        脑图生成接口 
        入参: 文章内容 or 文章id
        生成markdown格式的文章思维导图
    Args:
        content:str 文档内容 优先使用
        document_url:str 文档url  ip:address/bucket的名字/文件的名字

    Returns:
        success->bool: 是否成功 True or False
        msg->str: 成功或失败的消息
        data->str: 生成结果
    """
    res_dict = {}
    req_info = await info.json()

    content = req_info.get('content', '')
    document_url = req_info.get('document_url', '')

    try:
        if len(document_url) or len(content):
            loop = asyncio.get_event_loop()
            success, message, results = await loop.run_in_executor(None, gen_mindmap, qwen2, content, document_url)
            res_dict['success'] = success
            res_dict['message'] = message
            res_dict['data'] = results
            return JSONResponse(content=res_dict, media_type='application/json')
        else:  # title 为空时
            res_dict['success'] = False
            res_dict['message'] = 'provided document or content is empty!'
            res_dict['data'] = ''
            return JSONResponse(content=res_dict, media_type='application/json')
    except Exception as e:
        print(e)
        res_dict['success'] = False
        res_dict['message'] = str(e)
        res_dict['data'] = ''
        return JSONResponse(content=res_dict, media_type='application/json')
            
if __name__ == "__main__":
    host = "0.0.0.0"     # Linux
    # host = '127.0.0.1'  # Windows.
    port = cfg.service_port
    uvicorn.run(app, host=host, port=port, log_config='./uviconfig.json')
