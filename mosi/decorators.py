from functools import wraps
import traceback

from flask import redirect, flash, url_for, request, render_template, Blueprint
from flask import current_app as app
from flask_security import login_required, roles_accepted, current_user
#from skal.models import (Beernight, BeernightBeer)
from mosi.models import (ABtest, Mos, Sus, MosInstance, SusObject)
from flask_principal import Identity, Permission, RoleNeed, identity_changed


def roles_accepted_2(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            for r in roles:
                if current_user.has_role(r):
                    return f(*args, **kwargs)
            return redirect(url_for('user.current_user_detail'))
        return wrapper
    return decorator


def organiser_of_abtest_or_admin(func):
    @wraps(func)
    def wrapper(abtest_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        ab_test = ABtest.query.get(abtest_id)
        is_admin = ab_test.is_user_admin(current_user.id) or current_user.is_admin()
        if not is_admin:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(abtest_id=abtest_id, *args, **kwargs)
    return wrapper

def organiser_of_mos_or_admin(func):
    @wraps(func)
    def wrapper(mos_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        mos = Mos.query.get(mos_id)
        is_admin = mos.is_user_admin(current_user.id) or current_user.is_admin()
        if not is_admin:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(mos_id=mos_id, *args, **kwargs)
    return wrapper

def organiser_of_mos_instance_or_admin(func):
    @wraps(func)
    def wrapper(mos_instance_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))

        instance = MosInstance.query.get(mos_instance_id)
        mos = Mos.query.get(instance.mos_id)
        is_admin = mos.is_user_admin(current_user.id) or current_user.is_admin()
        if not is_admin:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(mos_instance_id=mos_instance_id, *args, **kwargs)
    return wrapper

def organiser_of_sus_or_admin(func):
    @wraps(func)
    def wrapper(sus_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        sus = Sus.query.get(sus_id)
        is_admin = sus.is_user_admin(current_user.id) or current_user.is_admin()
        if not is_admin:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(sus_id=sus_id, *args, **kwargs)
    return wrapper

def organiser_of_sus_instance_or_admin(func):
    @wraps(func)
    def wrapper(sus_instance_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))

        instance = SusObject.query.get(sus_instance_id)
        sus = Sus.query.get(instance.sus_id)
        is_admin = sus.is_user_admin(current_user.id) or current_user.is_admin()
        if not is_admin:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(sus_instance_id=sus_instance_id, *args, **kwargs)
    return wrapper

'''
def member_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_member = beernight.is_user_member(current_user.id)
        if not is_member:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper

def not_member_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_member = beernight.is_user_member(current_user.id)
        if is_member:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper


def creator_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_creator = beernight.is_user_creator(current_user.id)
        if not is_creator:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper

def member_of_or_public_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        beernight = Beernight.query.get(beernight_id)
        if beernight.is_public:
            return func(beernight_id=beernight_id, *args, **kwargs)
        if current_user.is_authenticated:
            is_member = beernight.is_user_member(current_user.id)
            if is_member:  
                return func(beernight_id=beernight_id, *args, **kwargs)
        flash("Ekki heimilað.", category="danger")
        return redirect(url_for('user.current_user_detail'))
    return wrapper


def member_public_invite_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        beernight = Beernight.query.get(beernight_id)
        if beernight.is_public:
            return func(beernight_id=beernight_id, *args, **kwargs)
        if current_user.is_authenticated:
            is_member = beernight.is_user_member(current_user.id)
            invites = beernight.invitations
            is_invite = False
            for i in invites:
                if i.receiver_id == current_user.id:
                    is_invite = True
            if is_member or is_invite:  
                return func(beernight_id=beernight_id, *args, **kwargs)
        flash("Ekki heimilað.", category="danger")
        return redirect(url_for('user.current_user_detail'))
    return wrapper

'''