
from email_validator import validate_email as validate_email_format, EmailNotValidError
from flask_wtf import *
from wtforms import *
from wtforms.validators import DataRequired, Email


class RegisterForm(FlaskForm):
    email = StringField('Электронная Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    nickname = StringField('Никнейм', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироватся')