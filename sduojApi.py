import asyncio
import json
from typing import Union

import requests
from fastapi_cache.decorator import cache

from const import NACOS_addr, NACOS_namespace, SDUOJ_TOKEN

requestHeaders = {"sduoj-token": SDUOJ_TOKEN}


# @cache(expire=60)
async def getService_ip_port(server_name):
    data = requests.get(
        "http://" + NACOS_addr + "/nacos/v1/ns/instance/list",
        params={
            "serviceName": "DEFAULT_GROUP@@{}".format(server_name),
            "namespaceId": NACOS_namespace
        },
    ).json()
    r = data["hosts"][0]
    return r["ip"] + ":" + str(r["port"])


async def make_get(service, url, params) -> Union[dict, str]:
    addr = await getService_ip_port(service)
    data = requests.get(
        "http://" + addr + url,
        params=params,
        headers=requestHeaders
    ).content.decode(encoding="utf-8")
    try:
        data = json.loads(data)
    except:
        pass
    return data


async def make_post(service, url, params, data) -> Union[dict, str]:
    addr = await getService_ip_port(service)
    data = requests.post(
        "http://" + addr + url,
        params=params,
        json=data,
        headers=requestHeaders
    ).content.decode(encoding="utf-8")
    try:
        data = json.loads(data)
    except:
        pass
    return data


async def contestIdToGroupIdList(contestId):
    data = await make_get(
        "user-service",
        "/internal/group/contestIdToGroupIdList",
        {"contestId": contestId}
    )
    return data


async def examIdToGroupIdList(examId):
    data = await make_get(
        "user-service",
        "/internal/group/examIdToGroupIdList",
        {"examId": examId}
    )
    return data


async def getGroupMember(groupId):
    data = await make_get(
        "user-service",
        "/internal/group/query",
        {"groupId": groupId}
    )
    members = []
    for member in data['members']:
        members.append({'username': member['username'], 'email': member['email']})
    return members


async def getUserInformation(userId, mode):
    data = await make_get(
        "user-service",
        "/internal/user/userIdToUserSessionDTO",
        {"userId": userId}
    )
    if mode == 1:
        return {'username': data['username'], 'email': data['email']}
    elif mode == 0:
        return data


# username 查询 userId （固定的数据信息，不会改变）
async def getUserId(username):
    data = await make_get(
        "user-service",
        "/internal/user/usernameToUserId",
        {"username": username}
    )
    return data
# async def main():
#     # print(await getGroupMember(2))
#     print(await getUserInformation(1))
# asyncio.run(main())
