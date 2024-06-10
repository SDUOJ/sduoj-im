import ast
import json
import time
from http.cookies import SimpleCookie
import requests
from fastapi import Request, HTTPException, Depends

from model.redis_db import redis_client


def oj_information():  # 用来判断用户oj是否登录并获取user_id
    # 获取特定的 cookie 数据
    # token = request.cookies.get("SESSION")
    token = '1-0cfe7218-6387-457d-9e78-e1f785dde888'
    if token is not None:
        user_session_key = f'cache:sessions:{token}'
        user_information = json.loads(json.loads(redis_client.hget(user_session_key, 'sessionAttr:SDUOJUserInfo')))
    else:
        raise HTTPException(
            status_code=401,
            detail="用户未登录"
        )
    return user_information
