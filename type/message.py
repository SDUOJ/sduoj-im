from pydantic import BaseModel, ConfigDict
from type.notice import base_interface


class message_add_interface(base_interface):
    m_from : int
    m_to : int
    m_content : str
