from data import db_session
from data.users import User
from werkzeug.security import generate_password_hash

db_session.global_init("db/all_date.db")
db_sess = db_session.create_session()

for user in db_sess.query(User).all():
    if not user.password.startswith('scrypt:'):  # type: ignore 
        user.password = generate_password_hash(user.password) # type: ignore
        print(f"Обновлён пароль для {user.nickname}")

db_sess.commit()