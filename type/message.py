from pydantic import BaseModel, ConfigDict
from type.notice import base_interface


class message_group_interface(BaseModel):
    mg_id: int


class message_receive_interface(message_group_interface):
    m_content: str


class message_add_interface(message_receive_interface):
    u_id: int


class message_group_add_interface(base_interface):
    u_id: int
