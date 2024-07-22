from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case, not_
from model.db import dbSession
from model.group import Contest, Exam


class ContestExamModel(dbSession):
    def get_role_group(self, ct_id, e_id):
        with self.get_db() as session:
            if ct_id is not None:
                role_group_id = session.query(Contest.g_id).filter(
                    Contest.ct_id == ct_id
                ).first()
            elif e_id is not None:
                role_group_id = session.query(Exam.g_id).filter(
                    Exam.e_id == e_id
                ).first()
            session.commit()
            return role_group_id[0]
