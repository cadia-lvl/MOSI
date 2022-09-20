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
from mosi.models import (ABTuple, User, db, MosInstance, ABInstance, ABtest, ABRating, CustomRecording,
                         CustomToken, MosRating, Sus, SusObject, SusAnswer)


def save_custom_wav_for_abtest(zip, zip_name, tsv_name, abtest, id):
    # Create parent folders if missing (this should probably be done somewhere else)
    pathlib.Path(app.config["AB_AUDIO_DIR"]).mkdir(exist_ok=True)
    pathlib.Path(app.config["AB_RECORDING_DIR"]).mkdir(exist_ok=True)
    namelist = zip.namelist()
    with zip.open(tsv_name) as tsvfile:
        wav_path_dir = app.config["AB_AUDIO_DIR"]+"{}".format(id)
        webm_path = app.config["AB_RECORDING_DIR"]+"{}".format(id)
        mc = tsvfile.read()
        c = csv.StringIO(mc.decode())
        rd = csv.reader(c, delimiter=";")
        pathlib.Path(wav_path_dir).mkdir(exist_ok=True)
        pathlib.Path(webm_path).mkdir(exist_ok=True)
        uploaded_obj = []
        
        
        for row in rd:
            zip_info_curr = None
            if row[0] and (len(row) == 7 or len(row) == 8):
                # Validate columns
                if not ((row[1].lower() == 's' or row[1].lower() == 'r') and row[2]):
                    continue
                if not (row[3] == "1" or row[3] == "0"):
                    continue
                if len(row) >= 7 and not (row[4] and row[5]):
                    continue

                filepath = namelist[0] + 'audio/' + row[0]
                if not filepath in namelist:
                    continue
                
                for zipinfo in zip.filelist:
                    path_file = os.path.abspath(zipinfo.filename)
                    if path_file.endswith(filepath):
                        zip_info_curr = zipinfo
                        break
                if not zip_info_curr:
                    continue
                filename = os.path.basename(filepath)
                if True:
                    custom_token_name = '{}_m{:09d}'.format(
                        zip_name, id)
                    custom_token = CustomToken(
                        row[2], custom_token_name)
                    custom_recording = CustomRecording(custom_token)
                    
                    if len(row) == 7:
                        ab_instance = ABInstance(
                            custom_recording=custom_recording,
                            is_reference=True if row[3] == "1" else False,
                            model_idx=row[4],
                            utterance_idx=row[5],
                            voice_idx=row[6])
                    if len(row) == 8:
                        ab_instance = ABInstance(
                            custom_recording=custom_recording,
                            is_reference=True if row[3] == "1" else False,
                            model_idx=row[4],
                            utterance_idx=row[5],
                            voice_idx=row[6],
                            question=row[7])
                    db.session.add(custom_token)
                    db.session.add(custom_recording)
                    db.session.add(ab_instance)
                    db.session.flush()
                    file_id = '{}_s{:09d}_m{:09d}'.format(
                        os.path.splitext(
                            os.path.basename(filename))[0],
                        custom_recording.id, id)
                    fname = secure_filename(f'{file_id}.webm')
                    path = os.path.join(
                        app.config['AB_RECORDING_DIR'],
                        str(id), fname)
                    wav_path = os.path.join(
                        app.config['AB_AUDIO_DIR'],
                        str(id),
                        secure_filename(f'{file_id}.wav'))
                    zip_info_curr.filename = secure_filename(
                        f'{file_id}.wav')
                    zip.extract(zip_info_curr, wav_path_dir)
                    if(os.path.exists(wav_path)):
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
                        uploaded_obj.append(ab_instance)
                    else:
                        print('Not extracted correctly')
                        db.session.delete(custom_token)
                        db.session.delete(custom_recording)
                        db.session.delete(ab_instance)       
        db.session.commit()
        return uploaded_obj


def save_custom_wav(zip, zip_name, tsv_name, mos, id):
    # Create parent folders if missing (this should probably be done somewhere else)
    pathlib.Path(app.config["MOS_AUDIO_DIR"]).mkdir(exist_ok=True)
    pathlib.Path(app.config["MOS_RECORDING_DIR"]).mkdir(exist_ok=True)

    with zip.open(tsv_name) as tsvfile:
        wav_path_dir = app.config["MOS_AUDIO_DIR"]+"{}".format(id)
        webm_path = app.config["MOS_RECORDING_DIR"]+"{}".format(id)
        mc = tsvfile.read()
        c = csv.StringIO(mc.decode())
        rd = csv.reader(c, delimiter=";")
        pathlib.Path(wav_path_dir).mkdir(exist_ok=True)
        pathlib.Path(webm_path).mkdir(exist_ok=True)
        uploaded_obj = []
        for row in rd:
            if row[0] and (len(row) >= 3):
                # Validate columns
                if not ((row[1].lower() == 's' or row[1].lower() == 'r') and row[2]):
                    continue
                if len(row) >= 5 and not (row[3] and row[4] and row[4].isnumeric()):
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
                        if len(row) == 3:
                            mos_instance = MosInstance(
                                custom_recording=custom_recording)
                        elif len(row) == 4:
                            mos_instance = MosInstance(
                                custom_recording=custom_recording,
                                voice_id=row[3])
                        elif len(row) == 5:
                            mos_instance = MosInstance(
                                custom_recording=custom_recording,
                                voice_id=row[3],
                                utterance_idx=row[4])
                        elif len(row) == 6:
                            mos_instance = MosInstance(
                                custom_recording=custom_recording,
                                voice_id=row[3],
                                utterance_idx=row[4],
                                model_idx=row[5])
                        elif len(row) == 7:
                            mos_instance = MosInstance(
                                custom_recording=custom_recording,
                                voice_id=row[3],
                                utterance_idx=row[4],
                                model_idx=row[5],
                                additional_id=row[6])
                        elif len(row) == 8:
                            mos_instance = MosInstance(
                                custom_recording=custom_recording,
                                voice_id=row[3],
                                utterance_idx=row[4],
                                model_idx=row[5],
                                additional_id=row[6],
                                question=row[7])
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
                            app.config['MOS_RECORDING_DIR'],
                            str(id), fname)
                        wav_path = os.path.join(
                            app.config['MOS_AUDIO_DIR'],
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
                        uploaded_obj.append(mos_instance)
                
        if len(uploaded_obj) > 0:
            db.session.commit()

        return uploaded_obj

def save_custom_sus_wav(zip, zip_name, tsv_name, sus, id):
    # Create parent folders if missing (this should probably be done somewhere else)
    pathlib.Path(app.config["SUS_AUDIO_DIR"]).mkdir(exist_ok=True)
    pathlib.Path(app.config["SUS_RECORDING_DIR"]).mkdir(exist_ok=True)
    wav_path_dir = app.config["SUS_AUDIO_DIR"]+"{}".format(id)
    webm_path = app.config["SUS_RECORDING_DIR"]+"{}".format(id)
    pathlib.Path(wav_path_dir).mkdir(exist_ok=True)
    pathlib.Path(webm_path).mkdir(exist_ok=True)
    uploaded_obj = []
    if tsv_name in zip.namelist():
        with zip.open(tsv_name) as tsvfile:
            mc = tsvfile.read()
            c = csv.StringIO(mc.decode())
            rd = csv.reader(c, delimiter=";")
            for row in rd:
                if row[0] and len(row) == 2:
                    for zip_info in zip.infolist():
                        if zip_info.filename[-1] == '/':
                            continue
                        filename, file_extension = os.path.splitext(zip_info.filename)
                        if not file_extension == '.wav':
                            continue
                        zip_info.filename = os.path.basename(zip_info.filename)
                        if zip_info.filename == row[0]:
                            custom_token_name = '{}_m{:09d}'.format(
                                zip_name, id)
                            
                            custom_token = CustomToken(
                                row[1], custom_token_name)
                            custom_recording = CustomRecording(custom_token)
                            
                            sus_object = SusObject(
                                custom_recording=custom_recording)
                            db.session.add(custom_token)
                            db.session.add(custom_recording)
                            db.session.add(sus_object)
                            db.session.flush()
                            file_id = '{}_s{:09d}_m{:09d}'.format(
                                os.path.splitext(
                                    os.path.basename(zip_info.filename))[0],
                                custom_recording.id, id)
                            fname = secure_filename(f'{file_id}.webm')
                            path = os.path.join(
                                app.config['SUS_RECORDING_DIR'],
                                str(id), fname)
                            wav_path = os.path.join(
                                app.config['SUS_AUDIO_DIR'],
                                str(id),
                                secure_filename(f'{file_id}.wav'))
                            zip_info.filename = secure_filename(
                                f'{file_id}.wav')
                            zip.extract(zip_info, wav_path_dir)
                            sound = AudioSegment.from_wav(wav_path)
                            sound.export(path, format="webm")
                            custom_recording.original_fname = secure_filename(row[0])
                            custom_recording.user_id = current_user.id
                            custom_recording.file_id = file_id
                            custom_recording.fname = fname
                            custom_recording.path = path
                            custom_recording.wav_path = wav_path
                            if row[1].lower() == 's':
                                sus_object.is_synth = True
                            else:
                                sus_object.is_synth = False
                            sus.sus_objects.append(sus_object)
                            uploaded_obj.append(sus_object)
                            break
    else:
        for zip_info in zip.infolist():
            if zip_info.filename[-1] == '/':
                continue
            filename, file_extension = os.path.splitext(zip_info.filename)
            if not file_extension == '.wav':
                continue
            zip_info.filename = os.path.basename(zip_info.filename)

            custom_token_name = '{}_m{:09d}'.format(
                zip_name, id)
            
            custom_token = CustomToken(
                '', custom_token_name)
            custom_recording = CustomRecording(custom_token)
            
            sus_object = SusObject(
                custom_recording=custom_recording)
            db.session.add(custom_token)
            db.session.add(custom_recording)
            db.session.add(sus_object)
            db.session.flush()
            file_id = '{}_s{:09d}_m{:09d}'.format(
                os.path.splitext(
                    os.path.basename(zip_info.filename))[0],
                custom_recording.id, id)
            fname = secure_filename(f'{file_id}.webm')
            path = os.path.join(
                app.config['SUS_RECORDING_DIR'],
                str(id), fname)
            wav_path = os.path.join(
                app.config['SUS_AUDIO_DIR'],
                str(id),
                secure_filename(f'{file_id}.wav'))
            zip_info.filename = secure_filename(
                f'{file_id}.wav')
            zip.extract(zip_info, wav_path_dir)
            sound = AudioSegment.from_wav(wav_path)
            sound.export(path, format="webm")
            custom_recording.original_fname = secure_filename(zip_info.filename)
            custom_recording.user_id = current_user.id
            custom_recording.file_id = file_id
            custom_recording.fname = fname
            custom_recording.path = path
            custom_recording.wav_path = wav_path
            sus.sus_objects.append(sus_object)
            uploaded_obj.append(sus_object)
    if len(uploaded_obj) > 0:
        db.session.commit()

        return uploaded_obj


def is_valid_MOS_rating(rating):
    if int(rating) > 0 and int(rating) <= 5:
        return True
    return False


def is_valid_abtest_rating(rating):
    if int(rating) > 0 and int(rating) <= 2:
        return True
    return False

def delete_MOS_rating_if_exists(mos_instance_id, user_id):
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
            if is_valid_MOS_rating(i['rating']):
                delete_MOS_rating_if_exists(i['id'], user_id)
                mos_instance = MosInstance.query.get(i['id'])
                rating = MosRating()
                rating.rating = int(i['rating'])
                rating.user_id = user_id
                rating.placement = i['placement']
                mos_instance.ratings.append(rating)
    db.session.commit()
    return mos_id


def is_valid_SUS_answer(ans):
    if len(ans) > 0:
        return True
    return False

def delete_SUS_answer_if_exists(SUS_object_id, user_id):
    ans = SusAnswer.query\
        .filter(SusAnswer.sus_object_id == SUS_object_id) \
        .filter(SusAnswer.user_id == user_id).all()
    exists = False
    for r in ans:
        exists = True
        db.session.delete(r)
    db.session.commit()
    return exists

def compare_sus_answer(true_string, ans):
    if true_string.lower() == ans.lower():
        return 1
    return 0

def save_SUS_ratings(form, files):
    user_id = int(form['user_id'])
    sus_id = int(form['sus_id'])
    sus = Sus.query.get(sus_id)
    obj_ids = sus.get_all_object_ids
    for i in form.keys():
        if i == 'user_id' or i == 'sus_id':
            continue
        if int(i) in obj_ids:
            if is_valid_SUS_answer(form[i]):
                delete_SUS_answer_if_exists(i, user_id)
                sus_object = SusObject.query.get(i)
                ans = SusAnswer()
                ans.answer = form[i]
                ans.user_id = user_id
                ans.correct_Answer = compare_sus_answer(sus_object.text, form[i])
                sus_object.answers.append(ans)
    db.session.commit()
    return sus_id


def delete_abtest_rating_if_exists(ab_tuple_id, user_id):
    rating = ABRating.query\
        .filter(ABRating.ab_tuple_id== ab_tuple_id) \
        .filter(ABRating.user_id == user_id).all()
    exists = False
    for r in rating:
        exists = True
        db.session.delete(r)
    db.session.commit()
    return exists

def save_abtest_ratings(form, files):
    user_id = int(form['user_id'])
    abtest_id = int(form['abtest_id'])
    abtest_list = json.loads(form['abtest_list'])
    if len(abtest_list) == 0:
        return None
    for i in abtest_list:
        if "rating" in i:
            if is_valid_abtest_rating(i['rating']):
                delete_abtest_rating_if_exists(i['tuple']['id'], user_id)
                ab_tuple = ABTuple.query.get(i['tuple']['id'])
                rating = ABRating()
                rating.rating = int(i['rating'])
                rating.user_id = user_id
                rating.placement = i['placement']
                ab_tuple.ratings.append(rating)
    db.session.commit()
    return abtest_id

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

def delete_sus_object_db(instance):
    errors = []
    try:
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

def delete_abtest_user_ratings(user_id, abtest_id):
    abtest = ABtest.query.get(abtest_id)
    ratings = abtest.getAllUserRatings(user_id)
    errors = []
    try:
        for r in ratings:
            db.session.delete(r)
        db.session.commit()
    except Exception as error:
        errors.append("Remove from database error")
        print(f'{error}\n{traceback.format_exc()}')
    if errors:
        return False, errors
    return True, errors

def delete_sus_test_db(sus):
    errors = []
    try:
        for instance in sus.sus_objects:
            os.remove(instance.custom_recording.get_path())
    except Exception as error:
        errors.append("Remove from disk error")
        print(f'{error}\n{traceback.format_exc()}')
    try:
        db.session.delete(sus)
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
