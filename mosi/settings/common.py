import os

APP_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))

# these should all have a trailing slash
DATA_BASE_DIR = os.path.join(APP_ROOT, os.pardir, 'data/')
CUSTOM_RECORDING_DIR = os.path.join(DATA_BASE_DIR, 'recordings/')
AB_RECORDING_DIR = os.path.join(CUSTOM_RECORDING_DIR, 'abtest/')
MOS_RECORDING_DIR = os.path.join(CUSTOM_RECORDING_DIR, 'mos/')
SUS_RECORDING_DIR = os.path.join(CUSTOM_RECORDING_DIR, 'sus/')
ZIP_DIR = os.path.join(DATA_BASE_DIR, 'zips/')
TEMP_DIR = os.path.join(DATA_BASE_DIR, 'temp/')
WAV_CUSTOM_AUDIO_DIR = os.path.join(DATA_BASE_DIR, 'wav_audio/')
AB_AUDIO_DIR = os.path.join(WAV_CUSTOM_AUDIO_DIR, 'abtest/')
MOS_AUDIO_DIR = os.path.join(WAV_CUSTOM_AUDIO_DIR, 'mos/')
SUS_AUDIO_DIR = os.path.join(WAV_CUSTOM_AUDIO_DIR, 'sus/')

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