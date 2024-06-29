from typing import Union

from pydantic import BaseModel, ConfigDict


class base_interface(BaseModel):
    p_id: Union[int, None] = None
    ct_id: Union[int, None] = None


class notice_information_interface(BaseModel):
    n_title: str
    n_content: str


class notice_delete_interface(BaseModel):
    n_id: int


class notice_interface(base_interface, notice_information_interface):
    pass


class notice_add_interface(notice_interface):
    u_id: int


class notice_user_add_interface(notice_delete_interface):
    u_id: int


class notice_update_interface(notice_interface, notice_delete_interface):
    pass
