from pydantic import BaseModel, ConfigDict
from type.notice import base_interface

class message_get_interface(base_interface):
    m_to: int

class message_receive_interface(message_get_interface):
    m_content: str


class message_add_interface(message_receive_interface):
    m_from: int
