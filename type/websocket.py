from typing import Union

from pydantic import BaseModel, ConfigDict


class websocket_add_interface(BaseModel):
    username: str
    w_token: str
    w_browser: str


class missed_add_interface(BaseModel):
    username: str
    ms_key: str
