import datetime
import json
import math
import os
import traceback
from flask import current_app as app
import csv
from pydub import AudioSegment
from pydub.utils import mediainfo
import pathlib
from werkzeug import secure_filename
from collections import defaultdict
from flask import flash
from sqlalchemy import func
from flask_security import current_user
from mosi.models import (User, db, MosInstance, ABInstance, ABtest, ABRating, CustomRecording,
                         CustomToken, MosRating)


def save_custom_wav_for_abtest(zip, zip_name, tsv_name, abtest, id):
    # Create parent folders if missing (this should probably be done somewhere else)
    pathlib.Path(app.config["AB_AUDIO_DIR"]).mkdir(exist_ok=True)
    pathlib.Path(app.config["AB_RECORDING_DIR"]).mkdir(exist_ok=True)

    with zip.open(tsv_name) as tsvfile:
        wav_path_dir = app.config["AB_AUDIO_DIR"]+"{}".format(id)
        webm_path = app.config["AB_RECORDING_DIR"]+"{}".format(id)
        mc = tsvfile.read()
        c = csv.StringIO(mc.decode())
        rd = csv.reader(c, delimiter="\t")
        pathlib.Path(wav_path_dir).mkdir(exist_ok=True)
        pathlib.Path(webm_path).mkdir(exist_ok=True)
        custom_tokens = []
        for row in rd:
            if row[0] and (len(row) == 6 or len(row) == 7):
                # Validate columns
                if not ((row[1].lower() == 's' or row[1].lower() == 'r') and row[2]):
                    continue
                if not (row[3] == "1" or row[3] == "0"):
                    continue
                if len(row) >= 6 and not (row[4] and row[4].isnumeric() and row[5] and row[5].isnumeric()):
                    continue

                for zip_info in zip.infolist():
                    if zip_info.filename[-1] == '/':
                        continue
                    zip_info.filename = os.path.basename(zip_info.filename)
                    if zip_info.filename == row[0]:
                        custom_token_name = '{}_m{:09d}'.format(
                            zip_name, id)
                        custom_token = CustomToken(
                            row[2], custom_token_name)
                        custom_recording = CustomRecording(custom_token)
                        
                        if len(row) == 6:
                            ab_instance = ABInstance(
                                custom_recording=custom_recording,
                                is_reference=True if row[3] == "1" else False,
                                voice_idx=row[4],
                                utterance_idx=row[5])
                        if len(row) == 7:
                            ab_instance = ABInstance(
                                custom_recording=custom_recording,
                                is_reference=True if row[3] == "1" else False,
                                voice_idx=row[4],
                                utterance_idx=row[5],
                                question=row[6])
                        db.session.add(custom_token)
                        db.session.add(custom_recording)
                        db.session.add(ab_instance)
                        db.session.flush()
                        file_id = '{}_s{:09d}_m{:09d}'.format(
                            os.path.splitext(
                                os.path.basename(zip_info.filename))[0],
                            custom_recording.id, id)
                        fname = secure_filename(f'{file_id}.webm')
                        path = os.path.join(
                            app.config['AB_RECORDING_DIR'],
                            str(id), fname)
                        wav_path = os.path.join(
                            app.config['AB_AUDIO_DIR'],
                            str(id),
                            secure_filename(f'{file_id}.wav'))
                        zip_info.filename = secure_filename(
                            f'{file_id}.wav')
                        zip.extract(zip_info, wav_path_dir)
                        sound = AudioSegment.from_wav(wav_path)
                        sound.export(path, format="webm")
                        custom_recording.original_fname = row[0]
                        custom_recording.user_id = current_user.id
                        custom_recording.file_id = file_id
                        custom_recording.fname = fname
                        custom_recording.path = path
                        custom_recording.wav_path = wav_path
                        if row[1].lower() == 's':
                            ab_instance.is_synth = True
                        else:
                            ab_instance.is_synth = False
                        abtest.ABtest_objects.append(ab_instance)
        
        if len(custom_tokens) > 0:
            db.session.commit()
        
        return custom_tokens


def save_custom_wav(zip, zip_name, tsv_name, mos, id):
    # Create parent folders if missing (this should probably be done somewhere else)
    pathlib.Path(app.config["WAV_CUSTOM_AUDIO_DIR"]).mkdir(exist_ok=True)
    pathlib.Path(app.config["CUSTOM_RECORDING_DIR"]).mkdir(exist_ok=True)
    pathlib.Path(app.config["CUSTOM_TOKEN_DIR"]).mkdir(exist_ok=True)

    with zip.open(tsv_name) as tsvfile:
        wav_path_dir = app.config["WAV_CUSTOM_AUDIO_DIR"]+"{}".format(id)
        webm_path = app.config["CUSTOM_RECORDING_DIR"]+"{}".format(id)
        mc = tsvfile.read()
        c = csv.StringIO(mc.decode())
        rd = csv.reader(c, delimiter="\t")
        pathlib.Path(wav_path_dir).mkdir(exist_ok=True)
        pathlib.Path(webm_path).mkdir(exist_ok=True)
        custom_tokens = []
        for row in rd:
            if row[0] and (len(row) == 3 or len(row) == 5 or len(row) == 6):
                # Validate columns
                if not ((row[1].lower() == 's' or row[1].lower() == 'r') and row[2]):
                    continue
                if len(row) >= 5 and not (row[3] and row[3].isnumeric() and row[4] and row[4].isnumeric()):
                    continue

                for zip_info in zip.infolist():
                    if zip_info.filename[-1] == '/':
                        continue
                    zip_info.filename = os.path.basename(zip_info.filename)
                    if zip_info.filename == row[0]:
                        custom_token_name = '{}_m{:09d}'.format(
                            zip_name, id)
                        custom_recording = CustomRecording()
                        custom_token = CustomToken(
                            row[2], custom_token_name)
                        if len(row) == 3:
                            mos_instance = MosInstance(
                                custom_token=custom_token,
                                custom_recording=custom_recording)
                        elif len(row) == 4:
                            mos_instance = MosInstance(
                                custom_token=custom_token,
                                custom_recording=custom_recording,
                                voice_idx=row[3])
                        elif len(row) == 5:
                            mos_instance = MosInstance(
                                custom_token=custom_token,
                                custom_recording=custom_recording,
                                voice_idx=row[3],
                                utterance_idx=row[4])
                        elif len(row) == 6:
                            mos_instance = MosInstance(
                                custom_token=custom_token,
                                custom_recording=custom_recording,
                                voice_idx=row[3],
                                utterance_idx=row[4],
                                question=row[5])
                        db.session.add(custom_token)
                        db.session.add(custom_recording)
                        db.session.add(mos_instance)
                        db.session.flush()
                        file_id = '{}_s{:09d}_m{:09d}'.format(
                            os.path.splitext(
                                os.path.basename(zip_info.filename))[0],
                            custom_recording.id, id)
                        fname = secure_filename(f'{file_id}.webm')
                        path = os.path.join(
                            app.config['CUSTOM_RECORDING_DIR'],
                            str(id), fname)
                        wav_path = os.path.join(
                            app.config['WAV_CUSTOM_AUDIO_DIR'],
                            str(id),
                            secure_filename(f'{file_id}.wav'))
                        zip_info.filename = secure_filename(
                            f'{file_id}.wav')
                        zip.extract(zip_info, wav_path_dir)
                        sound = AudioSegment.from_wav(wav_path)
                        sound.export(path, format="webm")
                        custom_recording.original_fname = row[0]
                        custom_recording.user_id = current_user.id
                        custom_recording.file_id = file_id
                        custom_recording.fname = fname
                        custom_recording.path = path
                        custom_recording.wav_path = wav_path
                        if row[1].lower() == 's':
                            mos_instance.is_synth = True
                        else:
                            mos_instance.is_synth = False
                        mos.mos_objects.append(mos_instance)
                        custom_tokens.append(custom_token)
                
        if len(custom_tokens) > 0:
            custom_token_dir = app.config["CUSTOM_TOKEN_DIR"]+"{}".format(id)
            pathlib.Path(custom_token_dir).mkdir(exist_ok=True)
            for token in custom_tokens:
                token.save_to_disk()
            db.session.commit()
        return custom_tokens


def is_valid_info(data):
    if 'collection_info' in data and \
            'text_info' in data and \
            'recording_info' in data and \
            'other' in data:
        if 'text' in data['text_info'] and \
                "session_id" in data["collection_info"] and \
                "recording_fname" in data["recording_info"] and \
                "text_marked_bad" in data["other"] and \
                "recording_marked_bad" in data["other"] and\
                "duration" in data["recording_info"]:
            return True
    return False



def is_valid_rating(rating):
    if int(rating) > 0 and int(rating) <= 5:
        return True
    return False


def delete_rating_if_exists(mos_instance_id, user_id):
    rating = MosRating.query\
        .filter(MosRating.mos_instance_id == mos_instance_id) \
        .filter(MosRating.user_id == user_id).all()
    exists = False
    for r in rating:
        exists = True
        db.session.delete(r)
    db.session.commit()
    return exists


def save_MOS_ratings(form, files):
    user_id = int(form['user_id'])
    mos_id = int(form['mos_id'])
    mos_list = json.loads(form['mos_list'])
    if len(mos_list) == 0:
        return None
    for i in mos_list:
        if "rating" in i:
            if is_valid_rating(i['rating']):
                delete_rating_if_exists(i['id'], user_id)
                mos_instance = MosInstance.query.get(i['id'])
                rating = MosRating()
                rating.rating = int(i['rating'])
                rating.user_id = user_id
                rating.placement = i['placement']
                mos_instance.ratings.append(rating)
    db.session.commit()
    return mos_id



def delete_mos_instance_db(instance):
    errors = []
    try:
        os.remove(instance.custom_token.get_path())
        os.remove(instance.custom_recording.get_path())
    except Exception as error:
        errors.append("Remove from disk error")
        print(f'{error}\n{traceback.format_exc()}')
    try:
        db.session.delete(instance)
        db.session.commit()
    except Exception as error:
        errors.append("Remove from database error")
        print(f'{error}\n{traceback.format_exc()}')
    if errors:
        return False, errors
    return True, errors

def delete_abtest_instance_db(instance):
    errors = []
    try:
        os.remove(instance.custom_token.get_path())
        os.remove(instance.custom_recording.get_path())
    except Exception as error:
        errors.append("Remove from disk error")
        print(f'{error}\n{traceback.format_exc()}')
    try:
        db.session.delete(instance)
        db.session.commit()
    except Exception as error:
        errors.append("Remove from database error")
        print(f'{error}\n{traceback.format_exc()}')
    if errors:
        return False, errors
    return True, errors

def delete_abtest_tuple_db(instance):
    errors = []
    try:
        db.session.delete(instance)
        db.session.commit()
    except Exception as error:
        errors.append("Remove from database error")
        print(f'{error}\n{traceback.format_exc()}')
    if errors:
        return False, errors
    return True, errors


def resolve_order(object, sort_by, order='desc'):
    ordering = getattr(object, sort_by)
    if callable(ordering):
        ordering = ordering()
    if str(order) == 'asc':
        return ordering.asc()
    else:
        return ordering.desc()


def activity(model):
    '''
    Returns two lists (x, y) where x contains timestamps
    and y contains the number of items of the given model
    that were created at the given day
    '''
    groups = ['year', 'month', 'day']
    groups = [func.extract(x, model.created_at).label(x) for x in groups]
    q = (
            db.session.query(func.count(model.id).label('count'), *groups)
            .group_by(*groups)
            .order_by(*groups)
            .all())
    x = [
            (lambda x: f'{int(x.day)}/{int(x.month)}/{int(x.year)}')(el)
            for el in q]
    y = [el.count for el in q]
    return x, y
