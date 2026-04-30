from flask_wtf import FlaskForm 
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField, FileField 
from wtforms.validators import DataRequired, Optional


class PostsForm(FlaskForm):
    label = StringField('Заголовок', validators=[DataRequired()])
    sublabel = StringField('*Подзаголовок')
    media_file = FileField('Видео/Аудио/Изображение', validators=[
        FileAllowed(
            ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'mov', 'avi', 'mp3', 'wav', 'ogg'],
            'Разрешены только изображения, видео и аудио!'
        )
    ])
    media_url = StringField('Или ссылка на файл (внешняя)', validators=[Optional()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное?")
    submit = SubmitField('Опубликовать')