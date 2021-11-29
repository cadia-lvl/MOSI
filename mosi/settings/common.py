import os

APP_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))

# these should all have a trailing slash
DATA_BASE_DIR = os.path.join(APP_ROOT, os.pardir, 'data/')
CUSTOM_TOKEN_DIR = os.path.join(DATA_BASE_DIR, 'custom_tokens/')
AB_TOKEN_DIR = os.path.join(CUSTOM_TOKEN_DIR, 'abtest/')
MOS_TOKEN_DIR = os.path.join(CUSTOM_TOKEN_DIR, 'mos/')
CUSTOM_RECORDING_DIR = os.path.join(DATA_BASE_DIR, 'recordings/')
AB_RECORDING_DIR = os.path.join(CUSTOM_RECORDING_DIR, 'abtest/')
MOS_RECORDING_DIR = os.path.join(CUSTOM_RECORDING_DIR, 'mos/')
ZIP_DIR = os.path.join(DATA_BASE_DIR, 'zips/')
TEMP_DIR = os.path.join(DATA_BASE_DIR, 'temp/')
WAV_CUSTOM_AUDIO_DIR = os.path.join(DATA_BASE_DIR, 'wav_audio/')
AB_AUDIO_DIR = os.path.join(WAV_CUSTOM_AUDIO_DIR, 'abtest/')
MOS_AUDIO_DIR = os.path.join(WAV_CUSTOM_AUDIO_DIR, 'mos/')

# Path to the logging file
LOG_PATH = os.path.join(APP_ROOT, os.pardir, 'logs', 'info.log')

# For other static files, like the LOBE manual
OTHER_DIR = os.path.join(APP_ROOT, os.pardir, 'other')
STATIC_DATA_DIR = os.path.join(OTHER_DIR, 'static_data/')
MANUAL_FNAME = 'LOBE_manual.pdf'

TOKEN_PAGINATION = 50
VERIFICATION_PAGINATION = 100
RECORDING_PAGINATION = 20
COLLECTION_PAGINATION = 20
USER_PAGINATION = 30
SESSION_PAGINATION = 50
CONF_PAGINATION = 30
MOS_PAGINATION = 20


SESSION_SZ = 50

RECAPTCHA_USE_SSL = False
RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECURITY_LOGIN_USER_TEMPLATE = 'login_user.jinja'

# The default configuration id stored in database
DEFAULT_CONFIGURATION_ID = 1

COLORS = {
    'common': "#bdbdbd",
    'rare': "#42a5f5",
    'epic': "#7e57c2",
    'legendary': "#ffc107",
    'danger': "#ff4444",
    'primary': "#0275d8",
    'success': "#5cb85c",
    'info': "#5bc0de",
    'warning': "#f0ad4e",
    'diamond': "#ff4444",
}


COLOR_PALETTE = {
    'first': "#261C2C",
    'second': "#3E2C41",
    'third': "#5C527F",
    'fourth': "#6E85B2",
    'fifth': "#ff4444",
}

ECONOMY = {
    'social_feed': {
        'post_youtube': 1000,
        'like': 100,
        'super_like': 250,
        'post_recording': 500,
    },
    'weekly_challenge': {
        'goal': 5000,
        'coin_reward': 300,
        'experience_reward': 3000,
        'extra_interval': 2000,
        'extra_coin_reward': 50,
        'extra_experience_reward': 200,
        'best_coin_reward': 500,
        'best_experience_reward': 5000,
    },
    'loot_boxes': {
        'prices': {
            '0': 100,
            '1': 200,
            '2': 300,
            '3': 400
        },
        'rarity_weights': {
            '0': 1,
            '1': 0.2,
            '2': 0.1,
            '3': 0.05,
        },
        'num_items': 3
    },
    'verification': {
        'coin_reward': 0,
        'experience_reward': 5
    },
    'session': {
        'coin_reward': 5,
        'experience_reward': 50,
    },
    'achievements': {
        'verification': {
            '0': {
                'title': 'Leiðangur hefst',
                'goal': 50,
                'coin_reward': 10,
                'experience_reward': 50,
                'fa_id': "fa fa-play"
            },
            '1': {
                'title': 'Upp á við',
                'goal': 500,
                'coin_reward': 50,
                'experience_reward': 100,
                'fa_id': "fa fa-check"
            },
            '2': {
                'title': 'Veggjaklifur',
                'goal': 1000,
                'coin_reward': 100,
                'experience_reward': 200,
                'fa_id': "fa fa-coins"
            },
            '3': {
                'title': 'Hástökk',
                'goal': 2000,
                'coin_reward': 200,
                'experience_reward': 300,
                'fa_id': "fa fa-gem"
            },
            '4': {
                'title': 'Everest',
                'goal': 5000,
                'coin_reward': 300,
                'experience_reward': 500,
                'fa_id': 'fa fa-crown',
            },
            '5': {
                'title': 'Út í geim',
                'goal': 15000,
                'coin_reward': 1000,
                'experience_reward': 10000,
                'fa_id': 'fa fa-user-astronaut',
            },
            '6': {
                'title': 'Út fyrir endimörk alheimsins',
                'goal': 30000,
                'coin_reward': 2000,
                'experience_reward': 20000,
                'fa_id': 'fa fa-rocket',
            }
        }, 'spy': {
            '0': {
                'title': 'Spæjaraskólinn',
                'goal': 10,
                'coin_reward': 10,
                'experience_reward': 50,
                'fa_id': 'fa fa-search'
            },
            '1': {
                'title': 'A+ í spæjarafræðum',
                'goal': 50,
                'coin_reward': 50,
                'experience_reward': 100,
                'fa_id': 'fa fa-binoculars'
            },
            '2': {
                'title': 'Fyrsta spæjaravinnan',
                'goal': 100,
                'coin_reward': 100,
                'experience_reward': 500,
                'fa_id': 'fa fa-user-tie'
            },
            '3': {
                'title': 'Yfirmaður spæjaradeildarinnar',
                'goal': 200,
                'coin_reward': 500,
                'experience_reward': 1500,
                'fa_id': 'fa fa-user-secret'
            },
            '4':{
                'title': 'Forseti spæjaraakademíunnar',
                'goal': 300,
                'coin_reward': 700,
                'experience_reward': 2500,
                'fa_id': 'fa fa-university'
            },
            '5':{
                'title': 'Nóbelsverðlaun í spæjarafræðum',
                'goal': 500,
                'coin_reward': 1000,
                'experience_reward': 5000,
                'fa_id': 'fa fa-medal'
            },
            '6':{
                'title': 'Drottnari spæjaraheimsins',
                'goal': 800,
                'coin_reward': 2500,
                'experience_reward': 8000,
                'fa_id': 'fas fa-crown'
            }
        },
        'streak_minimum': 500,
        'streak': {
            '0': {
                'title': 'Hlaupaskólinn',
                'goal': 1,
                'coin_reward': 10,
                'experience_reward': 50,
                'fa_id': 'fa fa-search'
            },
            '1': {
                'title': 'Hlaupaakademían',
                'goal': 2,
                'coin_reward': 50,
                'experience_reward': 100,
                'fa_id': 'fa fa-search'
            },
            '5': {
                'title': 'Hlaupaháskólinn',
                'goal': 2,
                'coin_reward': 50,
                'experience_reward': 100,
                'fa_id': 'fa fa-search'
            },
            '10': {
                'title': 'Hlaupaólympíuleikar',
                'goal': 2,
                'coin_reward': 50,
                'experience_reward': 100,
                'fa_id': 'fa fa-search'
            }
        }
    }
}
