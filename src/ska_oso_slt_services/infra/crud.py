# CRUD class
from backend.models.slt import SLT
from backend.models.slt_image import SLTImage
from backend.models.slt_log import SLTLogs


class CrudBase:
    def __init__(self, model, session_pool):
        self.model = model
        self.session_pool = session_pool

    def create(self, **kwargs):

        with self.session_pool() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def get(self, obj_id: int = None):
        with self.session_pool() as session:
            if obj_id:
                return session.query(self.model).filter(self.model.id == obj_id).first()
            else:
                return session.query(self.model).all()

    def update(self, obj_id: int, **kwargs):
        with self.session_pool() as session:
            obj = session.query(self.model).filter(self.model.id == obj_id).first()
            if obj:
                for key, value in kwargs.items():
                    setattr(obj, key, value)
                session.commit()
                session.refresh(obj)
            return obj

    def delete(self, obj_id: int):
        with self.session_pool() as session:
            obj = session.query(self.model).filter(self.model.id == obj_id).first()
            if obj:
                session.delete(obj)
                session.commit()
            return obj

    def join_get(self):
        with self.session_pool() as session:
            obj = session.query(self.model, SLT).join(SLT).all()
            return obj


class CrudSlt(CrudBase):
    def __init__(self):
        super().__init__(SLT)


class CrudSltLogs(CrudBase):
    def __init__(self):
        super().__init__(SLTLogs)


class CrudSltImage(CrudBase):
    def __init__(self):
        super().__init__(SLTImage)
