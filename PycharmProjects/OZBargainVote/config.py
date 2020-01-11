class Config:
    DEBUG = False
    REDIS_CONF = {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'decode_responses': 'utf-8'
    }
    SECRET_KEY = 'dev'


class DevelopmentConfig(Config):
    DEBUG = True
