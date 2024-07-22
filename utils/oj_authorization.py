import ast
import json
import time
from http.cookies import SimpleCookie
from typing import Union

import requests
from fastapi import Request, HTTPException, Depends
from fastapi import FastAPI, WebSocket
from model.redis_db import redis_client


def oj_http_authorization(request: Request):  # 权限认证方法
    token = request.cookies.get("SESSION")
    # token = '1-0cfe7218-6387-457d-9e78-e1f785dde888'
    try:
        if token is not None:
            user_session_key = f'cache:sessions:{token}'
            user_information = json.loads(json.loads(redis_client.hget(user_session_key, 'sessionAttr:SDUOJUserInfo')))
            return user_information if user_information == '' else None
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="用户未登录"
        )
    # if judge_type == 0:
    #     return user_information
    # elif judge_type == 1:


def oj_websocket_authorization(websocket: WebSocket):  # 用来鉴权 ( 0为验证是否登录 ; 1为验证用户是否是组成员 ; 2为验证是否为组管理员 )
    # 获取特定的 cookie 数据
    token = websocket.cookies.get("SESSION")
    # token = '1-0cfe7218-6387-457d-9e78-e1f785dde888'
    try:
        if token is not None:
            user_session_key = f'cache:sessions:{token}'
            user_information = json.loads(json.loads(redis_client.hget(user_session_key, 'sessionAttr:SDUOJUserInfo')))
            return user_information if user_information == '' else None
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="用户未登录"
        )
