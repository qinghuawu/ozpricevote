from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from config import DevelopmentConfig
from redis import StrictRedis

redis_cli = StrictRedis(**DevelopmentConfig.REDIS_CONF)


class User(UserMixin):
    def __init__(self, user_id=-1):
        self.username = ''
        self.id = user_id
        self.password_hash = ''

    def register(self, username, password):
        self.username = username
        if redis_cli.hget('user:index', self.username):
            return False
        self.id = redis_cli.incr('user:id')
        redis_cli.hset('user:index', self.username, self.id)  # 会和hget冲突，需锁或watch
        self.set_password(password)
        redis_cli.hmset(f'user:info:{self.id}', {'name': self.username, 'password': self.password_hash})
        return True

    def retrieve_user(self, username):
        self.username = username
        self.id = redis_cli.hget('user:index', self.username)
        if not self.id:
            return False
        user = redis_cli.hgetall(f'user:info:{self.id}')
        self.password_hash = user['password']
        return self

    def retrieve_user_by_id(self):
        user = redis_cli.hgetall(f'user:info:{self.id}')
        if not user:
            return False
        self.username = user['name']
        self.password_hash = user['password']
        return self

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)