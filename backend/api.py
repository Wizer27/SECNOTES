from fastapi import FastAPI,HTTPException,Depends,Request,status,Header
from pydantic import BaseModel
import uvicorn
from typing import Optional
import json
import hashlib
import hmac
import os
from dotenv import load_dotenv
import time
from database.core import register,login

#init
load_dotenv()
app  = FastAPI()

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


@app.get("/")

async def main():
    return "SECNOTES API"

class UsernameOnly(BaseModel):
    username:str

class RegiterLogin(BaseModel):
    username:str
    hash_psw:str

@app.post("/register")
async def register_endpoint(req:RegiterLogin,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = await register(req.username,req.hash_psw)
        if not res:
            raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "User already exists")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")

@app.post("/login")
async def login_endpoint(req:RegiterLogin,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = await login(req.username,req.hash_psw)
        if not res:
            raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "User already exists")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")
#run
if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)
