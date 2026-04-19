from data import db_session
from data.users import User
from data.posts import Posts
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import *
from forms.registation_form import RegisterForm
from forms.login_form import LoginForm
from forms.post_form import PostsForm
import secrets
import os
db_path = os.path.join(os.path.dirname(__file__), 'db', 'all_date.db')


app = Flask(__name__)


login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'hunter_slime_key'
db_session.global_init(db_path)

def notify_admin(user):
    try:
        token = secrets.token_urlsafe(32)
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(user.id)
        if not user:
            return

        user.confirmation_token = token # type: ignore
        db_sess.commit()

        confirm_url = url_for('confirm_email', token=token, _external=True)

        print("НОВАЯ РЕГИСТРАЦИЯ — ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ")
        print(f"Имя: {user.nickname}")
        print(f"Email: {user.email}")
        print(f"Токен: {token}")
        print(f"Ссылка для подтверждения: {confirm_url}")
        
    except Exception as e:
        print("Ошибка в notify_admin:", str(e))
    finally:
        db_sess.close()
 
@app.route("/notify_user")       
def notify_user():
    return "Для подтверждения почты ваш запрос на регистрацию отправлен админу\nв скором времени он вам отправит ссылку для поодтверждения почты"

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)
    
@app.route('/login', methods=['GET', 'POST'])
def login():# type: ignore
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user is not None:
            if user.check_password(form.password.data) and user.confirmed:   # type: ignore
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            elif not user.confirmed:   # type: ignore
                return render_template('login.html',
                                message="Неподтверждённый пользователь",
                                form=form)
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route("/")
def index():
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts)
    if current_user.is_authenticated:
        posts = db_sess.query(Posts).filter(
        (Posts.writer == current_user.nickname) | (Posts.is_private != True))
    else:
        posts = db_sess.query(Posts).filter(Posts.is_private != True)
    return render_template("index.html", posts=posts)



    
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter((User.email == form.email.data)).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с этой почтой уже есть")
        if db_sess.query(User).filter((User.nickname == form.nickname.data)).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким никнеймом уже есть")
        user = User(
            email=form.email.data,
            nickname=form.nickname.data,
            position_in_access="User",
            confirmation_token = None
            )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        user_id = user.id
        db_sess.close()
        notify_admin(user)
        return redirect('/login')  
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/confirm_email/<token>') # pyright: ignore[reportArgumentType]
def confirm_email(token):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.confirmation_token == token).first()
    if user:
        user.confirmed = True # type: ignore
        user.confirmation_token = None # type: ignore
        db_sess.merge(user)
        db_sess.commit()
        db_sess.close()
        return "Email подтверждён можете зайти на ваш аккаунт"
    else:
        return "Что-то пошло не так"
    
@app.route('/post_a_post',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = PostsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        post = Posts(
        writer = current_user.nickname,
        label = form.label.data,
        sublabel = form.sublabel.data,
        text = form.content.data,
        is_private = form.is_private.data)
        db_sess.add(post)
        db_sess.commit()
        return redirect('/')
    return render_template('post.html', title='Добавление новости', 
                           form=form)

@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = PostsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                          Posts.writer == current_user.nickname).first()
        if posts:
            form.label.data = posts.label # type: ignore
            form.sublabel.data = posts.sublabel # type: ignore
            form.content.data = posts.text # type: ignore
            form.is_private.data = posts.is_private # type: ignore
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                          Posts.writer == current_user.nickname).first()
        if posts:
            posts.label = form.label.data # type: ignore
            posts.sublabel = form.sublabel.data # type: ignore
            posts.text = form.content.data # type: ignore
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('post.html',
                           title='Редактирование поста',
                           form=form)

@app.route('/post_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).filter(Posts.id == id,
                                      Posts.writer == current_user.nickname).first()
    if posts:
        db_sess.delete(posts)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
     app.run(port=8080, host='127.0.0.1')

