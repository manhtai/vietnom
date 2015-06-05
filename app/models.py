from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask.ext.login import UserMixin, AnonymousUserMixin

from flask.ext.misaka import markdown
import bleach
import hashlib

from app import db, login_manager, cache


class Permission:
    VIEW = 0x01
    VOTE = 0x02
    TELL = 0x04
    CENSOR = 0x08
    GANGSTER = 0x80


class Role(db.Model):
    """Role for dear Users"""
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        """Bit-wise `OR` using here for make role, that is, everyone in higher
        order should have higher power, including all lower ones
        """
        roles = {
            'Voter': (Permission.VIEW |
                      Permission.VOTE, False),
            'Teller': (Permission.VIEW |
                      Permission.VOTE |
                     Permission.TELL, True),
            'Communist': (Permission.VIEW |
                          Permission.VOTE |
                          Permission.TELL |
                          Permission.CENSOR, False),
            'Gangster': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class Vote(db.Model):
    """Who want to vote? Every must
    User vote Post is a many-to-many relationship because one user cant vote
    many post, and one post can vote by many user

    So we must create a separated table to keep one-to-one relationship between
    one user and one post, because one user should vote once for one post
    """
    __tablename__ = 'votes'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'),
                        primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    vote = db.Column(db.Integer)


class User(UserMixin, db.Model):
    """Who are you, my user?"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # Which role are you?
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    # Things you should keep for yourself if you can't keep your mouth shut
    enabled = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    url = db.Column(db.String(64))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    votes = db.relationship('Vote',
                            foreign_keys=[Vote.user_id],
                            backref=db.backref('voter', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['MAIL_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    @cache.memoize(60*5)
    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    @cache.memoize(60*5)
    def is_administrator(self):
        return self.can(Permission.GANGSTER)

    @cache.memoize(60*5)
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @cache.memoize(60*60)
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return '<User %r>' % self.username

    def up(self, post):
        v = self.is_vote(post)
        if v is None:
            v = Vote(user_id=self.id, post_id=post.id, vote=1)
            db.session.add(v)
        elif v.vote == 1:
            db.session.delete(v)
        else:
            db.session.delete(v)
            v = Vote(user_id=self.id, post_id=post.id, vote=1)
            db.session.add(v)

    def down(self, post):
        v = self.is_vote(post)
        if v is None:
            v = Vote(user_id=self.id, post_id=post.id, vote=-1)
            db.session.add(v)
        elif v.vote == 1:
            db.session.delete(v)
            v = Vote(user_id=self.id, post_id=post.id, vote=-1)
            db.session.add(v)
        else:
            db.session.delete(v)

    @cache.memoize(60*5)
    def is_vote(self, post):
        return self.votes.filter_by(post_id=post.id).first()

    def is_up(self, post):
        u = self.is_vote(post)
        if u: return u.vote == 1

    def is_down(self, post):
        d = self.is_vote(post)
        if d: return d.vote == -1


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


class Post(db.Model):
    """Table for everyone's stories"""
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)

    keyword = db.Column(db.String(16))
    story = db.Column(db.Text)

    keyword_backup = db.Column(db.Text)
    story_backup = db.Column(db.Text)

    story_html = db.Column(db.Text)

    shared = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # Link to User and to Nom table
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    nom_id = db.Column(db.Integer, db.ForeignKey('noms.id'))
    # Link to Vote table, a bit tricky, huh?
    votes = db.relationship('Vote',
                            foreign_keys=[Vote.post_id],
                            backref=db.backref('voted', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')

    @cache.memoize(60*5)
    def up_count(self):
        """How many are you like me?"""
        return self.votes.filter_by(vote=1).count()

    @cache.memoize(60*5)
    def down_count(self):
        """How many are you dislike me?"""
        return self.votes.filter_by(vote=-1).count()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        """When user change body post, we update body_html to display them
        """
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'p',]
        target.story_html = bleach.clean(markdown(value),
                                         tags=allowed_tags,
                                         strip=True)
# This is the watcher for changing body post
db.event.listen(Post.story, 'set', Post.on_changed_body)

class Nom(db.Model):
    __tablename__ = 'noms'
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(7))
    keyword = db.Column(db.String(16))
    meaning = db.Column(db.Text)
    posts = db.relationship('Post', backref='nom', lazy='dynamic')
    ucn_code = db.Column(db.String(7))

    def __init__(self, **kwargs):
        super(Nom, self).__init__(**kwargs)
        if self.ucn_code is None:
            self.ucn_code = self.to_ucn()
    
    @property
    @cache.memoize(60*60)
    def count(self):
        return self.query.count()

    def to_ucn(self):
        """Convert Python Unicode to Universal Character Number
        Like this U+4032
        """
        ucn = self.character.encode('unicode_escape').decode('latin1')
        ucn = ucn.replace('\\', '').strip()
        if len(ucn) > int(4):
            ucn = ucn.lstrip("0")
        return ucn

    def to_json(self):
        """Export all Nom to JSON for Lunr.js search, yeah, I know, I should
        implement an server-side search soon
        """
        json = {"id": str(self.id),
                "c": self.character,
                "k": self.keyword}
        return json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
