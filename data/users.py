import datetime
import sqlalchemy
from flask_login import UserMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    nickname = sqlalchemy.Column(sqlalchemy.String, unique=True)
    message_for_other = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    avatar = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    position_in_access = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, 
                              index=True, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String)
    page_are_private = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, 
                                      default=datetime.datetime.now)
    
    confirmed = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    confirmation_token = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    
    posts = orm.relationship("Posts", back_populates='users')
    subscriptions = orm.relationship("Subs", back_populates='users')
    
    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return password == password