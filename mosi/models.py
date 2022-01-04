import contextlib
import os
import uuid
import wave
import json
import subprocess
import random
from collections import Counter, defaultdict

import numpy as np
from datetime import datetime, timedelta

from flask import current_app as app
from flask import url_for
from flask_security import RoleMixin, UserMixin
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from werkzeug import secure_filename

from wtforms_components import ColorField
from wtforms import validators

from mosi.tools.latin_square import balanced_latin_squares

db = SQLAlchemy()

ADMIN_ROLE_ID = 1
ADMIN_ROLE_NAME = "admin"
ESTIMATED_AVERAGE_RECORD_LENGTH = 5


class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self.__dict__.items()})
            



class CustomToken(BaseModel, db.Model):
    __tablename__ = 'CustomToken'

    def __init__(
            self, text,
            pron="Óþekkt", score=None, source="Upphleðsla"):
        self.text = text
        self.marked_as_bad = False
        self.pron = pron
        self.score = score
        self.source = source


    def get_url(self):
        return url_for('mos.custom_token', id=self.id)

    @hybrid_property
    def length(self):
        return len(self.text)

    def short_text(self, limit=20):
        if self.length < limit:
            return self.text
        else:
            return f'{self.text[:limit]}...'

    def get_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'url': self.get_url()}

    def get_printable_id(self):
        return "U-{:09d}".format(self.id)


    def get_download_url(self):
        return url_for('mos.download_custom_token', id=self.id)

    def copyToken(self, token):
        self.pron = token.pron
        self.score = token.score
        self.source = token.source

    @property
    def test_id(self):
        if self.mos_instance_id:
            return self.mosInstance.mos.id
        else:
            return self.ABInstance.ABtest.id

    @hybrid_property
    def test_obj(self):
        if self.mos_instance_id:
            return self.mosInstance.mos
        else: 
            return self.ABInstance.ABtest
        

    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    text = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    recordings = relationship("CustomRecording", back_populates="token")
    marked_as_bad = db.Column(db.Boolean, default=False)
    pron = db.Column(db.String)
    score = db.Column(db.Float, default=-1)
    source = db.Column(db.String)



class CustomRecording(BaseModel, db.Model):
    __tablename__ = 'CustomRecording'

    def __init__(self, token, copied_recording=False):
        self.token = token
        self.copied_recording = copied_recording

    def get_fname(self):
        return self.fname

    def get_download_url(self):
        return url_for('mos.download_custom_recording', id=self.id)

    def get_directory(self):
        return os.path.dirname(self.path)

    def get_path(self):
        return self.path

    def get_wav_path(self):
        return self.wav_path

    def get_zip_fname(self):
        if self.wav_path is not None:
            return os.path.split(self.wav_path)[1]
        return self.fname

    def get_zip_path(self):
        if self.wav_path is not None:
            return self.wav_path
        return self.path

    def copyRecording(self, recording):
        self.original_fname = recording.original_fname
        self.user_id = recording.user_id
        self.duration = recording.duration
        self.fname = recording.fname
        self.file_id = recording.file_id
        self.path = recording.path
        self.wav_path = recording.wav_path

    def get_configured_path(self):
        '''
        Get the path the program believes the token should be stored at
        w.r.t. the current TOKEN_DIR environment variable
        '''
        if self.mos_instance_id:
            path = os.path.join(
                app.config['MOS_RECORDING_DIR'],
                str(self.token.collection_id), self.fname)
        else: 
            path = os.path.join(
                app.config['AB_RECORDING_DIR'],
                str(self.token.collection_id), self.fname)
        return path

    def get_file_id(self):
        if self.fname is not None:
            return os.path.splitext(self.fname)[0]
        else:
            # not registered, (using) primary key
            return "nrpk_{:09d}".format(self.id)

    def get_user(self):
        return User.query.get(self.user_id)

    def get_printable_id(self):
        return "R-{:09d}".format(self.id)

    def get_printable_duration(self):
        if self.duration is not None:
            return "{:2.2f}s".format(self.duration)
        else:
            return "n/a"

    def _set_path(self):
        # TODO: deal with file endings
        self.file_id = '{}_s{:09d}_m{:09d}'.format(
            os.path.splitext(self.original_fname)[0], self.id, self.token_id)
        self.fname = secure_filename(f'{self.file_id}.webm')
        if self.mos_instance_id:
            self.path = os.path.join(
                app.config['MOS_RECORDING_DIR'],
                str(self.mosInstance.id), self.fname)
            self.wav_path = os.path.join(
                app.config['MOS_AUDIO_DIR'],
                str(self.mosInstance.id),
                secure_filename(f'{self.file_id}.wav'))
        else:
            self.path = os.path.join(
                app.config['AB_RECORDING_DIR'],
                str(self.mosInstance.id), self.fname)
            self.wav_path = os.path.join(
                app.config['AB_AUDIO_DIR'],
                str(self.mosInstance.id),
                secure_filename(f'{self.file_id}.wav'))

    def get_dict(self):
        if self.token is not None:
            return {'id': self.id, 'url': self.get_download_url(), 'token': self.token.get_dict()}
        else:
            return {'id': self.id, 'url': self.get_download_url(), 'text': self.text, 'file_id': ''}

    @property
    def custom_token(self):
        if self.mos_instance_id:
            return self.mosInstance.custom_token
        else:
            return self.ABInstance.custom_token

    @property
    def text(self):
        return self.token.text

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    original_fname = db.Column(db.String, default='Unknown')
    token_id = db.Column(db.Integer, db.ForeignKey('CustomToken.id'))
    token = db.relationship("CustomToken", back_populates="recordings")
    mos_instance_id = db.Column(db.Integer, db.ForeignKey("MosInstance.id"))
    AB_instance_id = db.Column(db.Integer, db.ForeignKey("ABInstance.id"))
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True)

    duration = db.Column(db.Float)
    copied_recording = db.Column(db.Boolean, default=False)
    fname = db.Column(db.String)
    file_id = db.Column(db.String)
    path = db.Column(db.String)
    wav_path = db.Column(db.String)


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True)
    uuid = db.Column(db.String)
    name = db.Column(db.String(255))
    email = db.Column(
        db.String(255),
        unique=True)
    password = db.Column(db.String(255))
    sex = db.Column(db.String(255))
    age = db.Column(db.Integer)
    dialect = db.Column(db.String(255))
    audio_setup = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp())
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic'))
    #db.relationship(
    #    "ABRating", lazy='joined', backref="User",
    #    cascade='all, delete, delete-orphan')

    def get_url(self):
        return url_for('user.user_detail', id=self.id)

    def get_printable_name(self):
        if self.name is not None:
            return self.name
        else:
            return "Nafnlaus notandi"

    def is_admin(self):
        return self.has_role(ADMIN_ROLE_NAME)

    def __str__(self):
        if type(self.name) != str:
            return str("User_{}".format(self.id))
        return self.name

    def get_meta(self):
        '''
        Returns a dictionary of values that are included in meta.json
        when downloading collections
        '''
        return {
            'id': self.id,
            'name': self.get_printable_name(),
            'email': self.email,
            'sex': self.sex,
            'age': self.age,
            'dialect': self.dialect}


class Mos(BaseModel, db.Model):
    __tablename__ = 'Mos'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uuid = db.Column(db.String)
    question = db.Column(db.String)
    form_text = db.Column(db.String)
    help_text = db.Column(db.String)
    done_text = db.Column(db.String)
    use_latin_square = db.Column(db.Boolean, default=False)
    show_text_in_test = db.Column(db.Boolean, default=True)
    num_samples = db.Column(db.Integer, default=0, info={
        'label': 'Fjöldi setninga'
    })
    mos_objects = db.relationship(
        "MosInstance", lazy='joined', backref="mos",
        cascade='all, delete, delete-orphan')
    num_participants = db.Column(db.Integer, default=0)

    def getAllRatings(self):
        ratings = []
        for m in self.mos_objects:
            for r in m.ratings:
                ratings.append(r)
        return ratings

    def getAllUserRatings(self, user_id):
        ratings = []
        for m in self.mos_objects:
            for r in m.ratings:
                if user_id == r.user_id:
                    ratings.append(r)
        return ratings

    def getAllUsers(self):
        ratings = self.getAllRatings()
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    def getAllVoiceIndices(self):
        voices = set()
        for sample in self.mos_objects:
            voices.add(sample.voice_idx)
        return voices

    def getAllUtteranceIndices(self):
        utterances = set()
        for sample in self.mos_objects:
            utterances.add(sample.utterance_idx)
        return utterances

    def getResultsByVoice(self):
        voice_ratings = defaultdict(list)
        for obj in self.mos_objects:
            for rating in obj.ratings:
                voice_ratings["No ID" if obj.voice_idx is None else obj.voice_idx].append(rating)
        return voice_ratings

    def getResultData(self):
        mos_data = [[
            "instance_id",
            "question",
            "utterance_idx",
            "voice_idx",
            "is_synth",
            "user",
            "name",
            "age",
            "audio_setup",
            "rating",
            "placement",
        ]]
        for obj in self.mos_objects:
            for rating in obj.ratings:
                mos_data.append([
                    obj.id,
                    obj.question if obj.question else "",
                    obj.utterance_idx if obj.utterance_idx else "",
                    obj.voice_idx if obj.voice_idx else "",
                    int(obj.is_synth),
                    rating.user_id if  rating.user_id else "",
                    rating.user.name if rating.user.name else "",
                    rating.user.age if rating.user.age else "",
                    rating.user.audio_setup if rating.user.audio_setup else "",
                    rating.rating if rating.rating else "",
                    rating.placement if rating.placement else ""
                ])
        return mos_data


    def getConfigurations(self):
        """
        Generates a Latin square of sentence-system combinations 
        based on the number of voices/systems being tested.

        Input: none
        Output: an array of arrays, each containing MosInstance objects, wherein each 
        MosInstance object refers to a particular voice rendering a particular utterance.
        This results in a balanced test, which should minimize the effect of each sentence
        and the carry-over effect of speakers on each other.
        """
        voices = list(self.getAllVoiceIndices())
        utterances = list(self.getAllUtteranceIndices())
        num_voices = len(list(voices))
        latinSquareRows = balanced_latin_squares(num_voices)
        configurations = []
        for row in latinSquareRows:
            configuration = []
            while len(configuration) < len(list(utterances)):
                configuration.extend([x for x in self.mos_objects if (
                        x.voice_idx == row[len(configuration) % len(row)]
                        and
                        x.utterance_idx == utterances[len(configuration)]
                    )])
            configurations.append(configuration)
        return configurations

    @property
    def custom_tokens(self):
        tokens = []
        for m in self.mos_objects:
            tokens.append(m.custom_token)
        return tokens

    @property
    def url(self):
        return url_for('mos.mos_detail', id=self.id)

    @property
    def printable_id(self):
        return "MOS-{:04d}".format(self.id)

    @property
    def edit_url(self):
        return url_for('mos.mos_edit', id=self.id)

    @property
    def number_selected(self):
        return sum(r.selected == True for r in self.mos_objects)

    def add_participant(self, user):
        if not self.num_participants:
            self.num_participants = 1
        else:
            self.num_participants += 1


class MosInstance(BaseModel, db.Model):
    __tablename__ = 'MosInstance'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    mos_id = db.Column(db.Integer, db.ForeignKey('Mos.id'))
    custom_recording = db.relationship(
        "CustomRecording", lazy="joined",
        backref=db.backref("mosInstance", uselist=False), uselist=False,
        cascade='all, delete, delete-orphan')
    ratings = db.relationship(
        "MosRating", lazy="joined", backref='mosInstance',
        cascade='all, delete, delete-orphan')
    is_synth = db.Column(db.Boolean, default=False)
    voice_idx = db.Column(db.Integer, default=0)
    utterance_idx = db.Column(db.Integer, default=0)
    question = db.Column(db.Text, default="")
    selected = db.Column(db.Boolean, default=False, info={
        'label': 'Hafa upptoku'})

    def __init__(self, custom_token, custom_recording, voice_idx=None, utterance_idx=None, question=None):
        self.custom_token = custom_token
        self.custom_recording = custom_recording
        self.voice_idx = voice_idx
        self.utterance_idx = utterance_idx
        self.question = question

    def getUserRating(self, user_id):
        for r in self.ratings:
            if r.user_id == user_id:
                return r.rating
        return None

    def getAllUsers(self):
        ratings = self.ratings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    def get_dict(self):
        token = None
        if self.token is not None:
            token = self.token.get_dict()
        return {
            'id': self.id,
            'token': token,
            'mos_id': self.mos_id,
            'path': self.path,
            'text': self.text,
            'is_synth': self.is_synth,
            'selected': self.selected,
            'voice_idx': self.voice_idx,
            'utterance_idx': self.utterance_idx,
        }

    @property
    def token(self):
        return self.custom_recording.token


    @property
    def path(self):
        return self.custom_recording.path

    @property
    def text(self):
        return self.token.text

    @property
    def mos(self):
        return Mos.query.get(self.mos_id)

    @property
    def get_printable_id(self):
        return "MOS-Setning {}".format(self.id)

    @property
    def name(self):
        return "MOS-Setning {}".format(self.id)

    @property
    def ajax_edit_action(self):
        return url_for('mos.mos_instance_edit', id=self.id)

    @property
    def average_rating(self):
        if(len(self.ratings) > 0):
            total_ratings = 0
            for i in self.ratings:
                total_ratings += i.rating
            total_ratings = total_ratings/len(self.ratings)
            return round(total_ratings, 2)
        else:
            return "-"

    @property
    def std_of_ratings(self):
        ratings = [r.rating for r in self.ratings]
        if len(ratings) == 0:
            return "-"
        ratings = np.array(ratings)
        return round(np.std(ratings), 2)

    @property
    def number_of_ratings(self):
        return len(self.ratings)


class MosRating(BaseModel, db.Model):
    __tablename__ = 'MosRating'
    __table_args__ = (
        db.UniqueConstraint('mos_instance_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    rating = db.Column(db.Integer, default=0, info={
        'label': 'Einkunn',
        'min': 0,
        'max': 5,
    })
    mos_instance_id = db.Column(db.Integer, db.ForeignKey("MosInstance.id"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", backref="mos_parents")
    placement = db.Column(db.Integer)

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_instance(self):
        return MosInstance.query.get(self.mos_instance_id)
    

class ABtest(BaseModel, db.Model):
    __tablename__ = 'ABtest'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uuid = db.Column(db.String)
    question = db.Column(db.String)
    form_text = db.Column(db.String)
    help_text = db.Column(db.String)
    done_text = db.Column(db.String)
    show_text_in_test = db.Column(db.Boolean, default=True)
    num_samples = db.Column(db.Integer, default=0, info={
        'label': 'Fjöldi setninga'
    })
    ABtest_objects = db.relationship(
        "ABInstance", lazy='joined', backref="ABtest",
        cascade='all, delete, delete-orphan')
    ABtest_tuples= db.relationship(
        "ABTuple", lazy='joined', backref="ABtest",
        cascade='all, delete, delete-orphan')
    num_participants = db.Column(db.Integer, default=0)

    def does_tuple_exist(self, first_id, second_id, ref_id=None):
        for t in self.ABtest_tuples:
            if not ref_id:
                if first_id == t.ab_instance_first_id and second_id == t.ab_instance_second_id and t.ab_instance_referance_id == None:
                    return True
            else:
                if first_id == t.ab_instance_first_id and second_id == t.ab_instance_second_id and ref_id == t.ab_instance_referance_id:
                    return True
        return False

    def getAllRatings(self):
        ratings = []
        for t in self.ABtest_tuples:
            for r in t.ratings:
                ratings.append(r)
        return ratings

    def getAllUserRatings(self, user_id):
        ratings = []
        for m in self.ABtest_objects:
            for r in m.ratings:
                if user_id == r.user_id:
                    ratings.append(r)
        return ratings

    def getAllUsers(self):
        ratings = self.getAllRatings()
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    def getAllVoiceIndices(self):
        voices = set()
        for sample in self.mos_objects:
            voices.add(sample.voice_idx)
        return voices

    def getAllUtteranceIndices(self):
        utterances = set()
        for sample in self.mos_objects:
            utterances.add(sample.utterance_idx)
        return utterances

    def getResultsByVoice(self):
        voice_ratings = defaultdict(list)
        for obj in self.ABtest_objects:
            for rating in obj.ratings:
                voice_ratings["No ID" if obj.voice_idx is None else obj.voice_idx].append(rating)
        return voice_ratings

    def getResultData(self):
        abtest_data = [[
            "tuple_id",
            "question",
            "rating_id",
            "utterance_idx",
            "first_clip_id",
            "first_clip_voice_idx",
            "first_clip_file_name",
            "second_clip_id",
            "second_clip_voice_idx",
            "second_clip_file_name",
            "reference_clip_id",
            "reference_clip_voice_idx",
            "reference_clip_file_name",
            "user_id",
            "user_name",
            "user_age",
            "audio_setup",
            "rating",
            "placement",
        ]]
        for obj in self.ABtest_tuples:
            for rating in obj.ratings:
                abtest_data.append([
                    obj.id if obj.id else "",
                    obj.question if obj.question else "",
                    rating.id if rating.id else "",
                    obj.utterance_idx if obj.utterance_idx else "",
                    obj.first.id if obj.first.id else "",
                    obj.first.voice_idx if obj.first.voice_idx else "",
                    obj.first.custom_recording.original_fname if obj.first.custom_recording.original_fname else "",
                    obj.second.id if obj.second.id else "",
                    obj.second.voice_idx if obj.second.voice_idx else "",
                    obj.second.custom_recording.original_fname if obj.second.custom_recording.original_fname else "",
                    obj.ref.id if obj.ref and obj.ref.id else "",
                    obj.ref.voice_idx if obj.ref and obj.ref.voice_idx else "",
                    obj.ref.custom_recording.original_fname if obj.ref and obj.ref.custom_recording.original_fname else "",
                    rating.user_id if rating.user_id else "",
                    rating.user.name if rating.user and rating.user.name else "",
                    rating.user.age if rating.user and rating.user.age else "",
                    rating.user.audio_setup if rating.user and rating.user.audio_setup else "",
                    rating.rating if rating.rating else "",
                    rating.placement if rating.placement else ""
                ])
        return abtest_data


    def getConfigurations(self):
        """
        Generates a Latin square of sentence-system combinations 
        based on the number of voices/systems being tested.

        Input: none
        Output: an array of arrays, each containing MosInstance objects, wherein each 
        MosInstance object refers to a particular voice rendering a particular utterance.
        This results in a balanced test, which should minimize the effect of each sentence
        and the carry-over effect of speakers on each other.
        """
        voices = list(self.getAllVoiceIndices())
        utterances = list(self.getAllUtteranceIndices())
        num_voices = len(list(voices))
        latinSquareRows = balanced_latin_squares(num_voices)
        configurations = []
        for row in latinSquareRows:
            configuration = []
            while len(configuration) < len(list(utterances)):
                configuration.extend([x for x in self.mos_objects if (
                        x.voice_idx == row[len(configuration) % len(row)]
                        and
                        x.utterance_idx == utterances[len(configuration)]
                    )])
            configurations.append(configuration)
        return configurations

    @property
    def custom_tokens(self):
        tokens = []
        for m in self.mos_objects:
            tokens.append(m.custom_token)
        return tokens

    @property
    def url(self):
        return url_for('abtest.abtest_detail', id=self.id)

    @property
    def printable_id(self):
        return "AB-{:04d}".format(self.id)

    @property
    def edit_url(self):
        return url_for('mos.mos_edit', id=self.id)

    @property
    def number_selected(self):
        return sum(r.selected == True for r in self.ABtest_tuples)

    def add_participant(self, user):
        if not self.num_participants:
            self.num_participants = 1
        else:
            self.num_participants += 1


class ABInstance(BaseModel, db.Model):
    __tablename__ = 'ABInstance'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    abtest_id = db.Column(db.Integer, db.ForeignKey('ABtest.id'))
    custom_recording = db.relationship(
        "CustomRecording", lazy="joined",
        backref=db.backref("ABInstance", uselist=False), uselist=False,
        cascade='all, delete, delete-orphan')
    tuple_first = db.relationship('ABTuple', backref='ab_instance_first', lazy = 'dynamic', foreign_keys = 'ABTuple.ab_instance_first_id')
    tuple_second = db.relationship('ABTuple', backref='ab_instance_second', lazy = 'dynamic', foreign_keys = 'ABTuple.ab_instance_second_id')
    tuple_reference = db.relationship('ABTuple', backref='ab_instance_referance', lazy = 'dynamic', foreign_keys = 'ABTuple.ab_instance_referance_id')
    
    is_reference = db.Column(db.Boolean, default=False)
    is_synth = db.Column(db.Boolean, default=False)
    voice_idx = db.Column(db.String(20), default="")
    utterance_idx = db.Column(db.String(20),default="")
    model_idx = db.Column(db.String(20), default="")
    question = db.Column(db.Text, default="")

    def __init__(self, custom_recording, voice_idx=None, model_idx=None, is_reference=False, utterance_idx=None, question=None):
        self.custom_recording = custom_recording
        self.voice_idx = voice_idx
        self.utterance_idx = utterance_idx
        self.is_reference = is_reference
        self.model_idx = model_idx
        self.question = question

    def getUserRating(self, user_id):
        for r in self.ratings:
            if r.user_id == user_id:
                return r.rating
        return None



    def getAllUsers(self):
        ratings = self.ratings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    def get_dict(self):
        token = None
        if self.custom_recording.token is not None:
            token = self.custom_recording.token.get_dict()
        return {
            'id': self.id,
            'token': token,
            'abtest_id': self.abtest_id,
            'path': self.path,
            'text': self.text,
            'is_synth': self.is_synth,
            'selected': self.selected,
            'voice_idx': self.voice_idx,
            'utterance_idx': self.utterance_idx,
        }

    @property
    def ratings(self):
        ratings = []
        for i in self.tuple_first:
            for r in i.ratings:
                ratings.append(r)
        for i in self.tuple_second:
            for r in i.ratings:
                ratings.append(r)
        return ratings

    @property
    def ab_stats(self):
        picked = 0
        not_picked = 0
        no_vote = 0
        for i in self.tuple_first:
            for r in i.ratings:
                if r.rating == 1:
                    picked += 1
                else:
                    not_picked += 1
        for i in self.tuple_second:
            for r in i.ratings:
                if r.rating == 2:
                    picked += 1
                else:
                    not_picked += 1
        return picked, not_picked

    
    @property
    def picked(self):
        picked, not_picked = self.ab_stats
        return picked

    @property
    def not_picked(self):
        picked, not_picked = self.ab_stats
        return not_picked

    @property
    def ab_ratio(self):
        picked, not_picked = self.ab_stats
        if picked + not_picked == 0:
            return 0
        return picked / (picked + not_picked)
    
    @property
    def ab_ratio_inverse(self):
        picked, not_picked = self.ab_stats
        if picked + not_picked == 0:
            return 0
        return 1 - (picked / (picked + not_picked))
    

    @property
    def path(self):
        return self.custom_recording.path

    @property
    def text(self):
        return self.custom_recording.token.text

    @property
    def token(self):
        return self.custom_recording.token

    @property
    def ABtest(self):
        return ABtest.query.get(self.abtest_id)

    @property
    def get_printable_id(self):
        return "AB-Setning-{}".format(self.id)

    @property
    def name(self):
        return "AB-Setning-{}".format(self.id)

    @property
    def average_rating(self):
        if(len(self.ratings) > 0):
            total_ratings = 0
            for i in self.ratings:
                total_ratings += i.rating
            total_ratings = total_ratings/len(self.ratings)
            return round(total_ratings, 2)
        else:
            return "-"

    @property
    def std_of_ratings(self):
        ratings = [r.rating for r in self.ratings]
        if len(ratings) == 0:
            return "-"
        ratings = np.array(ratings)
        return round(np.std(ratings), 2)

    @property
    def number_of_ratings(self):
        return len(self.ratings)


class ABTuple(BaseModel, db.Model):
    __tablename__ = 'ABTuple'
    __table_args__ = (
        db.UniqueConstraint('ab_instance_first_id', 'ab_instance_second_id', 'ab_instance_referance_id'),
      )
    
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    ratings = db.relationship(
        "ABRating", lazy='joined', backref="ABtuple",
        cascade='all, delete, delete-orphan')

    abtest_id = db.Column(db.Integer, db.ForeignKey('ABtest.id'))
    ab_instance_first_id = db.Column(db.Integer, db.ForeignKey("ABInstance.id"))
    ab_instance_second_id = db.Column(db.Integer, db.ForeignKey("ABInstance.id"))
    ab_instance_referance_id = db.Column(db.Integer, db.ForeignKey("ABInstance.id"))
    selected = db.Column(db.Boolean, default=False, info={
        'label': 'Hafa upptoku'})

    def __init__(self, abtest_id, ab_instance_first_id, ab_instance_second_id, ab_instance_referance_id=None):
        self.abtest_id = abtest_id
        self.ab_instance_first_id = ab_instance_first_id
        self.ab_instance_second_id = ab_instance_second_id
        self.ab_instance_referance_id = ab_instance_referance_id

    @property
    def first(self):
        return self.ab_instance_first
    
    @property
    def second(self):
        return self.ab_instance_second

    @property
    def ref(self):
        if self.ab_instance_referance_id:
            return self.ab_instance_referance
        else:
            return None

    @property
    def utterance_idx(self):
        return self.first.utterance_idx

    @property
    def question(self):
        return self.first.question

    @property
    def token(self):
        return self.first.custom_recording.token

    @property
    def text(self):
        return self.first.text

    @property
    def has_reference(self):
        return True if self.ab_instance_referance_id else False

    @property
    def ajax_edit_action(self):
        return url_for('abtest.abtest_tuple_edit', id=self.id)

    def get_dict(self):
        return {
            'id': self.id,
            'token': self.token.get_dict(),
            'abtest_id': self.abtest_id,
            'first_id': self.ab_instance_first_id,
            'second_id': self.ab_instance_second_id,
            'ref_id': self.ab_instance_referance_id,
            'has_ref': self.has_reference,
        }


class ABRating(BaseModel, db.Model):
    __tablename__ = 'ABRating'
    __table_args__ = (
        db.UniqueConstraint('ab_tuple_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    rating = db.Column(db.Integer, default=0, info={
        'label': 'Einkunn',
        'min': 0,
        'max': 2,
    })

    ab_tuple_id = db.Column(db.Integer, db.ForeignKey("ABTuple.id"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", backref="ab_parents")
    placement = db.Column(db.Integer)

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def ab_tuple(self):
        return ABTuple.query.get(self.ab_tuple_id)

    @property
    def test_id(self):
        print(self.ab_tuple.abtest_id)
        return self.ab_tuple.abtest_id


