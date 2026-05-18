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
from forms.search_user_form import SearchUserForm
from forms.search_post_form import SearchPostsForm
import secrets
from flask_mail import Mail, Message
import os
import uuid
from werkzeug.utils import secure_filename
db_path = os.path.join(os.path.dirname(__file__), 'db', 'all_date.db')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov', 'avi', 'mp3', 'wav', 'ogg'}


app = Flask(__name__)


login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'hunter_slime_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db_session.global_init(db_path)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_local_file(url):
    return url and url.startswith('/static/uploads/')

def notify_admin(user_id):
    try:
        token = secrets.token_urlsafe(32)
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(user_id)
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
    return """Для подтверждения почты ваш запрос на регистрацию отправлен админу
            в скором времени он вам отправит ссылку для поодтверждения почты
            Для помощи обращайтесь на почту: huntoi.dontwtitemepls@internet.ru"""

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
    query = db_sess.query(Posts).join(User, User.nickname == Posts.writer)
    if not current_user.is_authenticated:
        query = db_sess.query(Posts).filter(
        Posts.is_private == False, User.page_are_private == False)
    else:
        query = query.filter(
            (Posts.writer == current_user.nickname) | (Posts.is_private == False),
            (User.page_are_private == False) | (User.nickname == current_user.nickname)
        )
    posts = query.all()
    
    nicknames = {post.writer for post in posts}
    
    users_data = db_sess.query(User.nickname, User.avatar).filter(User.nickname.in_(nicknames)).all()
    avatars = {user.nickname: user.avatar for user in users_data}

    db_sess.close()
    
    return render_template("index.html", posts=posts[::-1], avatars=avatars)



    
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
        notify_admin(user_id)
        return redirect("/notify_user")  
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
        
        media_path = None
        
        if form.media_file.data:
            file = form.media_file.data
            if allowed_file(file.filename):
                name, ext = os.path.splitext(file.filename)
                filename = secure_filename(f"{current_user.nickname}_{uuid.uuid4().hex}{ext}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename) # type: ignore
                file.save(filepath)
                media_path = f"/static/uploads/{filename}"
        elif form.media_url.data.strip(): # type: ignore
            media_path = form.media_url.data.strip()  # type: ignore # Внешняя ссылка
        
        post = Posts(
        writer = current_user.nickname,
        label = form.label.data,
        sublabel = form.sublabel.data,
        additions = media_path,
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
    db_sess = db_session.create_session()
    post = db_sess.query(Posts).filter(Posts.id == id,
                                          Posts.writer == current_user.nickname
                                          ).first()
    if not post:
        db_sess.close()
        abort(404)
        
    form = PostsForm()
        
    if request.method == "GET":   
        form = PostsForm(obj=post)
        if post.additions and not is_local_file(post.additions): # type: ignore
            form.media_url.data = post.additions # type: ignore
        else:
            form.media_url.data = ""
        
    if form.validate_on_submit():
        media_path = None
        if form.media_file.data:
            file = form.media_file.data
            if allowed_file(file.filename):
                if post.additions and post.additions.startswith('/static/uploads/'): # type: ignore
                    old_path = os.path.join(app.root_path, post.additions[1:]) # type: ignore
                    if os.path.exists(old_path):
                        os.remove(old_path)
                name, ext = os.path.splitext(file.filename)
                filename = secure_filename(f"{current_user.nickname}_{uuid.uuid4().hex}{ext}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename) # type: ignore
                file.save(filepath)
                media_path = f"/static/uploads/{filename}" 
        elif form.media_url.data: # type: ignore
            if post.additions and is_local_file(post.additions): # type: ignore
                old_path = os.path.join(app.root_path, post.additions[1:]) # type: ignore
                if os.path.exists(old_path):
                    os.remove(old_path)
            media_path = form.media_url.data.strip() # type: ignore
        else:
            media_path = post.additions   # type: ignore
        
        if post:
            post.label = form.label.data # type: ignore
            post.sublabel = form.sublabel.data # type: ignore
            post.additions = media_path # type: ignore
            post.text = form.content.data # type: ignore
            post.is_private = form.is_private.data# type: ignore
            db_sess.commit()
            #next_page = request.form.get('next')
            #if next_page in ['/', f'/user/{current_user.nickname}', "/search/posts"]:
            #    return redirect(next_page)
            #else:
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
        if post.additions and post.additions.startswith('/static/uploads/'): # type: ignore
            os.remove(os.path.join(app.root_path, post.additions[1:])) # type: ignore
        db_sess.delete(post)
        db_sess.commit()
    else:
        abort(404)
    #next_page = request.form.get('next')
    #if next_page in ['/', f'/user/{current_user.nickname}', "'/search/posts'"]:
    #    return redirect(next_page)
    #else:
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
        
    nicknames = {post.writer for post in posts}
    
    users_data = db_sess.query(User.nickname, User.avatar).filter(User.nickname.in_(nicknames)).all()
    avatars = {user.nickname: user.avatar for user in users_data}

    is_subscribed = False
    if current_user.is_authenticated:
        sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first() # type: ignore
        if sub and sub.subscriptions: # type: ignore
            is_subscribed = name in sub.subscriptions.split()

    db_sess.close()
    return render_template('user_page.html', posts=posts[::-1], user=user, sub=is_subscribed, avatars=avatars)
    
@app.route('/user/edit', methods=['GET', 'POST']) # type: ignore
@login_required
def user_edit_profile():
    try:
        form = EditUserForm()
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.nickname == current_user.nickname).first()
        if request.method == "GET":
            form.message.data = user.message_for_other # type: ignore
            form.is_private.data = user.page_are_private # type: ignore
            form.avatar_url.data = user.avatar if user.avatar and not is_local_file(user.avatar) else "" # type: ignore
        if form.validate_on_submit():
            media_path = user.avatar # type: ignore
            if form.avatar.data:
                file = form.avatar.data
                print(type(form.avatar))
                if allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.nickname}_avatar")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename) # type: ignore
                    old_avatars = [
                    f for f in os.listdir(app.config['UPLOAD_FOLDER']) # type: ignore
                    if f.startswith(f"{current_user.nickname}_avatar.")
                    ]
                    for old in old_avatars:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old)) # type: ignore
                    file.save(filepath)
                    media_path = f"/static/uploads/{filename}"
            elif form.avatar_url.data.strip(): # type: ignore
                media_path = form.avatar_url.data.strip()   # type: ignore
            
            user.message_for_other = form.message.data # type: ignore
            user.avatar = media_path # type: ignore
            user.page_are_private = form.is_private.data # type: ignore
            db_sess.commit()
            
            login_user(user, force=True)
            db_sess.close()
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
        next_page = request.form.get('next')
        if next_page and next_page in ['/subscritions', f'/user/{name}']:
            return redirect(next_page)
        else:
            return redirect('/subscritions')
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
        list_of_subs = [name for name in sub.subscriptions.split() if name] # type: ignore
        users_data = db_sess.query(User.nickname, User.avatar).filter(User.nickname.in_(list_of_subs)).all()
        avatars = {user.nickname: user.avatar for user in users_data}
        db_sess.close()
        return render_template('subscriptions.html', header="Подписки", subs=list_of_subs, avatars=avatars)
    else:
        db_sess.close()
        return render_template('subscriptions.html', header="Подписки", subs=[])
    
@app.route("/subscritions/posts") # type: ignore
@login_required
def subs_posts():
    db_sess = db_session.create_session()
    sub = db_sess.query(Subs).filter(Subs.subscriber == current_user.nickname).first()
    posts = []
    list_of_subs = [name for name in sub.subscriptions.split() if name] # type: ignore
    query = db_sess.query(Posts).join(User, User.nickname == Posts.writer)
    if not sub or not list_of_subs:
        posts = []
    else:
        list_of_subs = sub.subscriptions.split()
        posts = query.filter(
        Posts.writer.in_(list_of_subs),
        (Posts.writer == current_user.nickname) | (Posts.is_private == False),
        (User.page_are_private == False) | (User.nickname == current_user.nickname)
        ).all()
    nicknames = {post.writer for post in posts}
    users_data = db_sess.query(User.nickname, User.avatar).filter(User.nickname.in_(nicknames)).all()
    avatars = {user.nickname: user.avatar for user in users_data}
    db_sess.close()
    return render_template('subs_posts.html', header="Подписки", posts=posts[::-1], avatars=avatars)
    
@app.route('/search/users', methods=['GET', 'POST']) # type: ignore
@login_required
def search_users():
    form = SearchUserForm()
    try:
        db_sess = db_session.create_session()
        if form.validate_on_submit():
            if form.name.data:
                users = db_sess.query(User).filter(User.nickname.contains(form.name.data)).all()
                return render_template('search_users.html',
                                       header="Поиск людей", 
                                       users=users, form=form)
            
            return render_template('search_users.html', 
                                    header="Поиск людей",
                                    message="Вы не ввели имя человека",
                                    form=form)
    except Exception as e:
        return render_template('search_users.html', 
                                       header="Поиск людей",
                                       message="Пошло что-то не так")
    return render_template('search_users.html', header="Поиск людей", form=form)

@app.route('/search/posts', methods=['GET', 'POST']) # type: ignore
@login_required
def search_posts():
    form = SearchPostsForm(request.args)
    posts = []
    message = None
    avatars = {}
    try:
        db_sess = db_session.create_session()
        query = db_sess.query(Posts)

        has_search_params = any([
            request.args.get('label'),
            request.args.get('sublabel'),
            request.args.get('content'),
            request.args.get('writer')
        ])
        if has_search_params:
            if form.label.data:
                query = query.filter(Posts.label.contains(form.label.data))

            if form.sublabel.data:
                query = query.filter(Posts.sublabel.contains(form.sublabel.data))

            if form.content.data:
                query = query.filter(Posts.text.contains(form.content.data))

            if form.writer.data:
                query = query.filter(Posts.writer.contains(form.writer.data))
            query = query.join(User, User.nickname == Posts.writer).filter(
                    (Posts.is_private == False) | (Posts.writer == current_user.nickname),
                   (User.page_are_private == False) | (User.nickname == current_user.nickname)
                )

            posts = query.all()
            
            nicknames = {post.writer for post in posts}
            users_data = db_sess.query(User.nickname, User.avatar).filter(User.nickname.in_(nicknames)).all()
            avatars = {user.nickname: user.avatar for user in users_data}

            if form.is_submitted() and not posts:
                message = "Ничего не найдено."
        else:
            pass
                
        db_sess.close()
        
        return render_template(
        'search_posts.html',
        form=form,
        posts=posts,
        avatars=avatars,
        message=message
        )
    except Exception as e:
        print(f"Ошибка в поиске постов: {e}")
        db_sess.close()
        return render_template('search_posts.html', form=form, message="Пошло что-то не так")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")