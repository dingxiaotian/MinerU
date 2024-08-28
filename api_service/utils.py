import os, sys
import re
import json
from typing import Tuple

import base64
import requests
from requests.exceptions import RequestException, HTTPError, Timeout, TooManyRedirects

# 单独debug时启用
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from magic_pdf.pipe.UNIPipe import UNIPipe
from magic_pdf.pipe.OCRPipe import OCRPipe
from magic_pdf.pipe.TXTPipe import TXTPipe
from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
from magic_pdf.rw.S3ReaderWriter import S3ReaderWriter
from magic_pdf.rw.AbsReaderWriter import AbsReaderWriter

def b64_decode(b64_str:str) -> bytes:
    byte_data = base64.b64decode(b64_str)
    return byte_data

def download_document(url: str, timeout: int=60) -> bytes:
    """
    下载文件并返回字节数据。
    
    Args:
        url (str): 文件的 URL。
        timeout (int): 请求超时时间（秒）。默认为 60 秒。

    Returns:
        bytes: 文件的字节数据。

    Raises:
        ValueError: 如果下载的文件不是 PDF。
        Exception: 如果遇到其他无法处理的错误。
    """
    try:
        # 发送 HTTP GET 请求
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # 如果响应的状态码不是 200，则抛出 HTTPError

        # # 检查响应的内容类型是否为PDF?
        # content_type = response.headers.get('Content-Type')
        # if 'application/pdf' not in content_type:
        #     raise ValueError(f"Expected a PDF file, but got {content_type}")

        # 返回文件的字节数据
        return response.content

    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Timeout as timeout_err:
        print(f"Request timed out: {timeout_err}")
    except TooManyRedirects as redirect_err:
        print(f"Too many redirects: {redirect_err}")
    except RequestException as req_err:
        print(f"An error occurred while making the request: {req_err}")
    except ValueError as val_err:
        print(f"Value error: {val_err}")
    except Exception as err:
        print(f"An unexpected error occurred: {err}")
    
    # 如果发生异常，返回 None
    return None

def replace_local_image_paths(markdown_text):
    """
    从Markdown文本中提取本地图片地址并替换为指定的URL地址。

    :param markdown_text: str, 包含Markdown内容的字符串
    :param base_url: str, 替换本地图片路径的基URL
    :return: str, 替换后的Markdown文本
    """   
    ak = os.getenv("AK", "")
    sk = os.getenv("SK", "")
    endpoint_url = os.getenv("ENDPOINT", "")
    bucket_name = os.getenv("S3_BUCKET", "")

    try:
        s3_reader_writer = S3ReaderWriter(
            ak, sk, endpoint_url, "auto", f"s3://{bucket_name}"
        )

        # 匹配Markdown中所有图片的正则表达式 ![alt text](path/to/image.jpg)
        image_pattern = re.compile(r'!\[.*?\]\((.+?\.(?:jpg|jpeg|png|gif))\)')

        # 找到所有图片路径
        local_image_paths = image_pattern.findall(markdown_text)

        for local_image_path in local_image_paths:
            if os.path.exists(local_image_path):
                with open(local_image_path, 'rb') as f:
                    img_data = f.read()
                    f_name = local_image_path.split('/')[-1]
                    s3_relative_path = f"s3://{bucket_name}/{f_name}"
                    # 上传图片到S3并获取URL
                    s3_reader_writer.write(
                        img_data,
                        s3_relative_path=s3_relative_path,
                        mode=AbsReaderWriter.MODE_BIN,
                    )
                    # get presigned url
                    s3_url = s3_reader_writer.generate_presigned_url(s3_relative_path=s3_relative_path)

                    if s3_url:
                        # 替换Markdown中的本地路径为S3 URL
                        markdown_text = markdown_text.replace(local_image_path, s3_url)

    except Exception as e:
        print(e)

    return markdown_text


def pdf_parse_main(pdf_bytes:bytes, parse_method:str='auto', out_img_path:str=None) -> Tuple[bool, str, dict]:
    """
    执行从 pdf 转换到 json、md 的过程，输出 md 和 json 文件

    :param pdf_bytes: .pdf文件数据
    :param parse_method: 解析方法， 共 auto、ocr、txt 三种，默认 auto，如果效果不好，可以尝试 ocr
    :param out_img_path: 解析pdf产生的图像存储位置 一般是临时目录
    """
    res_dict = {
        'markdown': '',
        'json': ''
    }

    if not out_img_path or not os.path.exists(out_img_path):
        msg = 'Output image path does not exist!'
        return False, msg, res_dict

    try:
        # 执行解析步骤
        image_writer = DiskReaderWriter(out_img_path)

        # 选择解析方式
        if parse_method == "auto":
            jso_useful_key = {"_pdf_type": "", "model_list": []}
            pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        elif parse_method == "txt":
            pipe = TXTPipe(pdf_bytes, [], image_writer)
        elif parse_method == "ocr":
            pipe = OCRPipe(pdf_bytes, [], image_writer)
        else:
            msg = "unknown parse method, only auto, ocr, txt allowed"
            return False, msg, res_dict

        # 执行分类
        pipe.pipe_classify()
        pipe.pipe_analyze()  # 版式解析
        # 执行解析
        pipe.pipe_parse()

        # 保存 text 和 md 格式的结果
        abs_img_path = os.path.abspath(out_img_path)
        content_list = pipe.pipe_mk_uni_format(abs_img_path, drop_mode="none")
        md_content = pipe.pipe_mk_markdown(abs_img_path, drop_mode="none")
        content = json.dumps(content_list, ensure_ascii=False)
        md_content = replace_local_image_paths(md_content)
        res_dict['markdown'] = md_content
        res_dict['json'] = content
        return True, 'success', res_dict
    except Exception as e:
        print(e)
        return False, str(e), res_dict

if __name__ == '__main__':
    pdf_path = r"/opt/models/RNNT.pdf"
    with open(pdf_path, 'rb') as f:
        content = f.read()

    out_path = "/opt/models/RNNT"
    pdf_parse_main(pdf_bytes=content, out_img_path=out_path)