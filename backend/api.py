from fastapi import FastAPI,HTTPException,Depends,Request,status
from pydantic import BaseModel
from typing import Optional
import json
import hashlib
import hmac
import os
from dotenv import load_dotenv
import time

load_dotenv()

def verify_signature(data:dict,signature:str,timestamp:str) -> bool:
    if int(time.time()) - int(timestamp) > 300:
        return False
    KEY = os.getenv("SIGNATURE")
    data_to_verify = data.copy()
    data_to_verify.pop("signature",None)
    data_str = json.dumps(data_to_verify,sort_keys = True,separators = (',',':'))
    expected = hmac.new(KEY.encode(),data_str.encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature,expected)


async def safe_get(req:Request):
    api = req.headers.get("X-API-KEY")
    api_key = os.getenv("API")
    if not api or not hmac.compare_digest(api,api_key):
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN,detail = "invalid signature")

