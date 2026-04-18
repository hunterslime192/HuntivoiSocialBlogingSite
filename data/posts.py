import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Posts(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    writer = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("users.nickname"))
    label = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    sublabel = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    additions = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_private = sqlalchemy.Column(sqlalchemy.BOOLEAN)
                                     
    users = orm.relationship("User")

    