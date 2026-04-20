from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class PostsForm(FlaskForm):
    label = StringField('Заголовок', validators=[DataRequired()])
    sublabel = StringField('*Подзаголовок')
    addition = StringField('*Картинка (Ссылка на картинку оканчивающаяся на формат)')
    content = TextAreaField("Содержание", validators=[DataRequired()])
    is_private = BooleanField("Личное?")
    submit = SubmitField('Применить')