import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Subs(SqlAlchemyBase):
    __tablename__ = 'subscriptions'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    subscriber = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("users.nickname"))
    subscriptions = sqlalchemy.Column(sqlalchemy.String, default="")
                                     
    users = orm.relationship("User")

    