from flask_wtf import *
from wtforms import *
from wtforms.validators import DataRequired


class EditUserForm(FlaskForm):
    message = TextAreaField("Информация", validators=[DataRequired()])
    is_private = BooleanField("Закрытая страница?")
    submit = SubmitField('Применить')