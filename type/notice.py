from pydantic import BaseModel, ConfigDict


class base_interface(BaseModel):
    p_id: int = None
    ct_id: int = None


class notice_add_interface(base_interface):
    u_id: int
    n_title: str
    n_content: str


class notice_update_interface(BaseModel):
    n_id: int
    n_title: str
    n_content: str
