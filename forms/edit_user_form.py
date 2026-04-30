from flask_wtf import FlaskForm 
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField, FileField 
from wtforms.validators import DataRequired, Optional


class EditUserForm(FlaskForm):
    message = TextAreaField("Информация", validators=[DataRequired()])
    avatar = FileField('Новое фото профиля', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения формата jpg, png, gif')
    ])
    avatar_url = StringField('Или ссылка на картинку аватара', validators=[Optional()])
    is_private = BooleanField("Закрытая страница?")
    submit = SubmitField('Применить')