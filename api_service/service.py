# -*- coding: utf-8 -*-

import os, sys
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 单独debug时启用
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from api_service.documents_router import document_router
from api_service.image_router import image_router
from api_service.web_router import website_router

import config as cfg

logger = logging.getLogger(__name__)

# initialize Fastapi application.
app = FastAPI()

if cfg.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers in the main app
app.include_router(document_router, prefix="/parse_document", tags=["Documents"])
app.include_router(image_router, prefix="/parse_image", tags=["Images"])
app.include_router(website_router, prefix="/parse_website", tags=["Website"])

if __name__ == "__main__":
    host = "0.0.0.0"     # Linux
    # host = '127.0.0.1'  # Windows.
    port = cfg.service_port
    uvicorn.run(app, host=host, port=port, log_config='./uviconfig.json')