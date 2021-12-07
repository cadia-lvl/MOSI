import datetime
import os
import json
import zipfile
import traceback
from random import randint

from flask import current_app as app


from mosi.tools.analyze import load_sample, find_segment
from mosi.models import User, db


def pseudo_unique():
    '''
    TODO: replace with something better.
    I used this to add some entropy to filenames in case multiple archives
    are created at the same time.
    '''
    return str(randint(10000, 99999))


class ZipManager:
    def __init__(self, collection):
        self.collection = collection
        self.meta_path = os.path.join(
            app.config['TEMP_DIR'],
            f'meta_{pseudo_unique()}.json')
        self.zf = zipfile.ZipFile(self.collection.zip_path, mode='w')

    def add_token(self, token):
        self.zf.write(token.get_path(), 'text/{}'.format(token.get_fname()))

    def add_recording(self, recording, user_id):
        self.zf.write(
            recording.get_zip_path(),
            'audio/{}/{}'.format(user_id, recording.get_zip_fname()))

    def add_recording_info(self, info_path):
        self.zf.write(info_path, 'info.json')

    def add_index(self, index_path):
        self.zf.write(index_path, 'index.tsv')

    def add_meta(self, speaker_ids):
        meta = {'speakers': []}
        for id in speaker_ids:
            meta['speakers'].append(User.query.get(id).get_meta())
        meta['collection'] = self.collection.get_meta()
        meta_f = open(self.meta_path, 'w', encoding='utf-8')
        json.dump(meta, meta_f, ensure_ascii=False, indent=4)
        meta_f.close()
        self.zf.write(self.meta_path, 'meta.json')

    def close(self):
        self.zf.close()

    def clean_up(self):
        os.remove(self.meta_path)


class IndexManager:
    def __init__(self):
        self.path = os.path.join(
            app.config['TEMP_DIR'],
            f'index_{pseudo_unique()}.tsv')
        self.index = open(self.path, 'w')
        self.is_closed = False

    def add(self, recording, token, user_name):
        self.index.write('{}\t{}\t{}\n'.format(
            user_name, recording.get_zip_fname(), token.get_fname()))

    def close(self):
        self.index.close()
        self.is_closed = True

    def clean_up(self):
        assert self.is_closed
        os.remove(self.path)

    def get_path(self):
        return self.path
