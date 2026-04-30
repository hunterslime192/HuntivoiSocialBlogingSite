from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class SearchPostsForm(FlaskForm):
    label = StringField('Заголовок')
    sublabel = StringField('*Подзаголовок')
    content = TextAreaField("Содержание")
    writer = StringField('Автор')
    submit = SubmitField('Найти')