from data import db_session
from data.users import User
from data.posts import Posts
from data.subs import Subs
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import *
from forms.registation_form import RegisterForm
from forms.login_form import LoginForm
from forms.post_form import PostsForm
from forms.edit_user_form import EditUserForm
import secrets
from flask_mail import Mail, Message
import os
db_path = os.path.join(os.path.dirname(__file__), 'db', 'all_date.db')

app = Flask(__name__)

app.config.update(
    MAIL_SERVER='smtp.mail.ru',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='huntoi.dontwtitemepls@internet.ru',
    MAIL_PASSWORD='secret >:)',
    MAIL_DEFAULT_SENDER=('HuBlog', 'huntoi.dontwtitemepls@internet.ru')
)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'hunter_slime_key'
db_session.global_init(db_path)

def send_confirmation_email(user_id):
    token = secrets.token_urlsafe(32)
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    if not user:
        return
    user.confirmation_token = token # type: ignore
    db_sess.commit()


    confirm_url = url_for('confirm_email', token=token, _external=True)
    msg = Message("Подтвердите ваш email", recipients=[user.email]) # type: ignore
    msg.body = f"Перейдите по ссылке, чтобы подтвердить почту: {confirm_url}"
    mail.send(msg)

    db_sess.close()

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
        (Posts.writer == current_user.nickname) | (Posts.is_private == False))
    else:
        posts = db_sess.query(Posts).join(
            User, User.nickname == Posts.writer
        ).filter(
            Posts.is_private == False,
            User.page_are_private == False)
    return render_template("index.html", posts=posts[::-1])



    
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
        send_confirmation_email(user_id)
        return redirect('/login')  
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/confirm_email/<token>') # pyright: ignore[reportArgumentType]
def confirm_email(token):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(
        User.confirmation_token == token).first()
    sub = Subs(subscriber=user.nickname) # type: ignore
    if user:
        user.confirmed = True # type: ignore
        user.confirmation_token = None # type: ignore
        db_sess.merge(user)
        db_sess.add(sub)
        db_sess.commit()
        db_sess.close()
        return "Email подтверждён можете зайти на ваш аккаунт"
    else:
        return "Что-то пошло не так"
    
@app.route('/post_a_post',  methods=['GET', 'POST'])
@login_required
def add_post():
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
def edit_post(id):
    form = PostsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                          Posts.writer == current_user.nickname
                                          ).first()
        if posts:
            form.label.data = posts.label # type: ignore
            form.sublabel.data = posts.sublabel # type: ignore
            form.addition.data = posts.additions # type: ignore
            form.content.data = posts.text # type: ignore
            form.is_private.data = posts.is_private # type: ignore
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                          Posts.writer == current_user.nickname
                                          ).first()
        if posts:
            posts.label = form.label.data # type: ignore
            posts.sublabel = form.sublabel.data # type: ignore
            posts.additions = form.addition.data # type: ignore
            posts.text = form.content.data # type: ignore
            posts.is_private = form.is_private.data# type: ignore
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('post.html',
                           title='Редактирование поста',
                           form=form)

@app.route('/post_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def post_delete(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Posts).filter(Posts.id == id,
                                      Posts.writer == current_user.nickname
                                      ).first()
    if post:
        db_sess.delete(post)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')

@app.route('/user')
@login_required
def your_profile():
    return redirect(f'/user/{current_user.nickname}')

@app.route('/user/<string:name>') # type: ignore
def user_profile(name):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).filter(Posts.writer == name)
    user = db_sess.query(User).filter(User.nickname == name).first()
    if not user:
        abort(404)

    is_subscribed = False
    if current_user.is_authenticated:
        sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first() # type: ignore
        if sub and sub.subscriptions: # type: ignore
            is_subscribed = name in sub.subscriptions.split()
    return render_template('user_page.html', posts=posts[::-1], user=user, sub=is_subscribed)
    
@app.route('/user/edit', methods=['GET', 'POST']) # type: ignore
@login_required
def user_edit_profile():
    try:
        form = EditUserForm()
        if request.method == "GET":
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.nickname == current_user.nickname).first()
        
            form.message.data = user.message_for_other # type: ignore
            form.is_private.data = user.page_are_private # type: ignore
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.nickname == current_user.nickname).first()
            user.message_for_other = form.message.data # type: ignore
            user.page_are_private = form.is_private.data # type: ignore
            db_sess.commit()
            return redirect('/user')
    except Exception as e:
        return render_template('user_edit.html',
                           title = 'Редактирование профиля', 
                           form=form, message="Что-то пошло не так")
    return render_template('user_edit.html',
                           title = 'Редактирование профиля', 
                           form=form) 

@app.route('/subscritions/add/<string:name>', methods=['GET', 'POST']) # type: ignore
@login_required
def add_sub(name):
    db_sess = db_session.create_session()
    sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first() # type: ignore
    try: 
        list_of_subs = sub.subscriptions.split()# type: ignore
        list_of_subs.append(name)
        sub.subscriptions = " ".join(list_of_subs) # type: ignore
        db_sess.commit()
        return redirect(f'/user/{name}')
    except Exception as e:
        return "Пошло что-то не так. Повторите ещё раз."
    
@app.route('/subscritions/del/<string:name>', methods=['GET', 'POST']) # type: ignore
@login_required
def del_sub(name):
    db_sess = db_session.create_session()
    sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first() # type: ignore
    try: 
        list_of_subs = sub.subscriptions.split()# type: ignore
        list_of_subs.remove(name)
        sub.subscriptions = " ".join(list_of_subs) # type: ignore
        db_sess.commit()
        return redirect(f'/user/{name}')
    except Exception as e:
        return "Пошло что-то не так. Повторите ещё раз."
    
@app.route('/subscritions/delall', methods=['GET', 'POST']) # type: ignore
@login_required
def delall_subs():
    db_sess = db_session.create_session()
    sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first() # type: ignore
    try: 
        sub.subscriptions = "" # type: ignore
        db_sess.commit()
        return redirect(f'/subscritions')
    except Exception as e:
        return "Пошло что-то не так. Повторите ещё раз."

@app.route('/subscritions') # type: ignore
@login_required
def subs():
    db_sess = db_session.create_session()
    sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first()
    if sub.subscriptions: # type: ignore
        list_of_subs = sub.subscriptions.split() # type: ignore
        return render_template('subscriptions.html', header="Подписки", subs=list_of_subs)
    else:
        return render_template('subscriptions.html', header="Подписки", subs=[])
     
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
     app.run(port=8080, host='127.0.0.1')
