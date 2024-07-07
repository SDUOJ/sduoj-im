import ast
import json
import time
from http.cookies import SimpleCookie
import requests
from fastapi import Request, HTTPException, Depends

from model.redis_db import redis_client


def oj_authorization(request: Request):  # 用来鉴权 ( 0为验证是否登录 ; 1为验证用户是否是组成员 ; 2为验证是否为组管理员 )
    # 获取特定的 cookie 数据
    token = request.cookies.get("SESSION")
    # token = '1-0cfe7218-6387-457d-9e78-e1f785dde888'
    if token is not None:
        user_session_key = f'cache:sessions:{token}'
        user_information = json.loads(json.loads(redis_client.hget(user_session_key, 'sessionAttr:SDUOJUserInfo')))
    else:
        raise HTTPException(
            status_code=401,
            detail="用户未登录"
        )
    return user_information
    # if judge_type == 0:
    #     return user_information
    # elif judge_type == 1:
