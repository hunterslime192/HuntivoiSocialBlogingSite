from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class SearchUserForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Искать')