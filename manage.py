import getpass
import os
import re
import sys
import json
import uuid
import traceback
import datetime
from shutil import copyfile
from tqdm import tqdm
from random import randrange
import random
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command, Manager
from flask_security.utils import hash_password
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from termcolor import colored
from collections import defaultdict

from mosi import app
from mosi.models import (User, Role, ABRating, ABTuple,
                         db, MosInstance, ABtest, Mos, Sus)
from mosi.tools.analyze import (load_sample, signal_is_too_high,
                                signal_is_too_low)
from mosi.db import delete_abtest_rating_if_exists


migrate = Migrate(app, db, compare_type=True)
manager = Manager(app)


class AddDefaultRoles(Command):
    def run(self):
        roles = [
            {
                "name": "admin",
                "description":
                    'Umsjónarhlutverk með aðgang að notendastillingum',
            },
            {
                "name": "Notandi",
                "description": 'Venjulegur notandi með grunn aðgang',
            },
            {
                "name": "Greinir",
                "description": 'Greinir með takmarkað aðgengi',
            },
            {
                "name": "ab_tester",
                "description": 'Notandi sem tekur AB próf',
            },
            {
                "name": "mos_tester",
                "description": 'Notandi sem tekur MOS próf',
            },
            {
                "name": "test_partitipant",
                "description": 'Notandi sem tekur eitthvað próf',
            },
            {
                "name": "organiser",
                "description": 'Notandi sem getur búið til próf',
            },

        ]
        existing_roles = [role.name for role in Role.query.all()]
        for i, r in enumerate(roles):
            if r["name"] not in existing_roles:
                role = Role()
                role.name = r["name"]
                role.description = r["description"]
                db.session.add(role)
                print("Creating role:", r["name"])

        db.session.commit()

class AddUser(Command):
    def run(self):
        email = input("Email: ")
        name = input("Name: ")
        password = get_pw()

        roles = Role.query.all()
        selected_roles = []
        if len(roles) > 0:
            role_select = None
            while role_select not in [r.id for r in roles]:
                print(role_select, [r.id for r in roles])
                print("Select a role")
                role_select = int(input("".join(["[{}] - {} : {}\n".format(
                    role.id, role.name, role.description) for role in roles])))
            selected_roles.append(Role.query.get(role_select).name)
        with app.app_context():
            try:
                app.user_datastore.create_user(
                    email=email, password=hash_password(password),
                    name=name, roles=selected_roles,
                    uuid=uuid.uuid4())
                db.session.commit()
                print("User with email {} has been created".format(email))
            except IntegrityError as e:
                print(e)


class changePass(Command):
    def run(self):
        email = input("Email: ")
        user = User.query.filter_by(email=email).all()
        assert len(user) == 1, "User with email {} was not found".format(email)
        user = user[0]
        password = get_pw()
        user.password = hash_password(password)
        db.session.commit()
        print("Password has been updated")


def get_pw(confirm=True):
    password = getpass.getpass("Password: ")
    if confirm:
        password_confirm = getpass.getpass("Repeat password: ")
        while password != password_confirm:
            print("Passwords must match")
            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Repeat password: ")
    return password

@manager.command
def add_mos_dummy_voice_ids():
    mos_instances = MosInstance.query.all()
    for m in mos_instances:
        if m.voice_idx is None:
            m.voice_idx = randrange(4)
        db.session.commit()

@manager.command
def create_db():
    db.create_all()
    db.session.commit()

@manager.command
def add_admin_defaults():
    abtests = ABtest.query.all()
    mos = Mos.query.all()
    sus = Sus.query.all()
    user = User.query.get(1)
    for ab in abtests:
        if not ab.admins:
            ab.admins.append(user)

    for m in mos:
        if not m.admins:
            m.admins.append(user)
    
    for s in sus:
        if not s.admins:
            s.admins.append(user)
    
    db.session.commit()


@manager.command
def add_dummy_user_ratings():
    abtest_id = 9
    abtest = ABtest.query.get(abtest_id)
    users = []
    for i in range(30):
        user_uuid = uuid.uuid4()
        email = "{}@mosi.is".format(user_uuid)
        new_user = app.user_datastore.create_user(
            name='testuser_{}'.format(i),
            email=email,
            password=None,
            uuid=user_uuid,
            audio_setup=None,
            roles=['ab_tester', 'test_partitipant']
        )
        abtest.add_participant(new_user)
        users.append(new_user)
    db.session.commit()


    abtest_list_all = ABTuple.query.filter(ABTuple.abtest_id == 9 and ABTuple.selected == True).all()
    for u in users:
        abtest_list = random.sample(abtest_list_all, 30)
        user_id = u.id
        if len(abtest_list) == 0:
            return None
        for i in abtest_list:
            delete_abtest_rating_if_exists(i.id, user_id)
            rating = ABRating()
            rand_rating = random.randint(1,2)
            rating.rating = int(rand_rating)
            rating.user_id = user_id
            rating.placement = random.randint(1,30)
            i.ratings.append(rating)
    db.session.commit()



class AddColumnDefaults(Command):
    def run(self):
        users = User.query.filter(User.uuid == None).all()
        for u in users:
            u.uuid = str(uuid.uuid4())
        



manager.add_command('db', MigrateCommand)
manager.add_command('add_user', AddUser)
manager.add_command('change_pass', changePass)
manager.add_command('add_default_roles', AddDefaultRoles)
manager.add_command('add_column_defaults', AddColumnDefaults)
#manager.add_command('add_mos_dummy_voice_ids', AddVoiceIds)


if __name__ == '__main__':
    manager.run()

