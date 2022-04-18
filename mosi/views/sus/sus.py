import json
import traceback
import random
import time
import uuid
import numpy as np
from zipfile import ZipFile
from operator import itemgetter

from flask import (Blueprint, Response, send_from_directory, request,
                   render_template, flash, redirect, url_for)
from flask import current_app as app
from flask_security import login_required, roles_accepted, current_user
from sqlalchemy.exc import IntegrityError
from mosi.decorators import (organiser_of_sus_or_admin, organiser_of_sus_instance_or_admin)

from mosi.models import (Sus, SusObject, User,
                         CustomToken, CustomRecording, db)
from mosi.db import (resolve_order, save_custom_sus_wav,
                     delete_sus_object_db)
#from mosi.forms import (SusSelectAllForm, SusUploadForm, SusItemSelectionForm,
#                        SusTestForm, SusForm, SusDetailForm)

from mosi.forms import SusUploadForm, SusDetailForm

sus = Blueprint(
    'sus', __name__, template_folder='templates')


@sus.route('/sus/')
@login_required
@roles_accepted('admin', 'organiser')
def sus_list():
    if current_user.is_admin():
        page = int(request.args.get('page', 1))
        sus_list = Sus.query.order_by(
                resolve_order(
                    Sus,
                    request.args.get('sort_by', default='created_at'),
                    order=request.args.get('order', default='desc')))\
            .paginate(page, per_page=app.config['MOS_PAGINATION'])
    else:
        sus_ids = current_user.get_sus_ids
        page = int(request.args.get('page', 1))
        abtest_list = Sus.query.filter(Sus.id.in_(sus_ids)).order_by(
                resolve_order(
                    Sus,
                    request.args.get('sort_by', default='created_at'),
                    order=request.args.get('order', default='desc')))\
            .paginate(page, per_page=app.config['MOS_PAGINATION'])
    return render_template(
        'sus_list.jinja',
        sus_list=sus_list,
        section='sus')



@sus.route('/sus/<int:sus_id>', methods=['GET', 'POST'])
@login_required
@organiser_of_sus_or_admin
def sus_detail(sus_id):
    sus = Sus.query.get(sus_id)
    form = SusUploadForm()
    #select_all_forms = [
    #    SusSelectAllForm(is_synth=True, select=True),
    #    SusSelectAllForm(is_synth=True, select=False),
    #    SusSelectAllForm(is_synth=False, select=True),
    #    SusSelectAllForm(is_synth=False, select=False),
    #]

    if request.method == 'POST':
        if form.validate():
            if(form.is_g2p.data):
                zip_file = request.files.get('files')
                with ZipFile(zip_file, 'r') as zip:
                    zip_name = zip_file.filename[:-4]
                    tsv_name = '{}/index.csv'.format(zip_name)
                    successfully_uploaded = save_custom_sus_wav(
                        zip, zip_name, tsv_name, sus, sus_id)
                    if successfully_uploaded and len(successfully_uploaded) > 0:
                        flash("Tókst að hlaða upp {} setningum.".format(
                            len(successfully_uploaded)),
                            category="success")
                    else:
                        flash(
                            "Ekki tókst að hlaða upp neinum setningum.",
                            category="warning")
                return redirect(url_for('sus.sus_detail', sus_id=sus_id))
            else:
                flash(
                    "Ekki tókst að hlaða inn skrá. Eingögnu hægt að hlaða inn skrám á stöðluðu formi.",
                    category="danger")
        else:
            flash(
                "Villa í formi, athugaðu að rétt sé fyllt inn og reyndu aftur.",
                category="danger")

    sus_list = SusObject.query.filter(SusObject.sus_id == sus_id).order_by(
            resolve_order(
                SusObject,
                request.args.get('sort_by', default='id'),
                order=request.args.get('order', default='desc'))).all()

    return render_template(
        'sus.jinja',
        sus=sus,
        sus_list=sus_list,
        #select_all_forms=select_all_forms,
        sus_form=form,
        section='sus')


@sus.route('/sus/<int:sus_id>/edit/detail', methods=['GET', 'POST'])
@login_required
@organiser_of_sus_or_admin
def sus_edit_detail(sus_id):
    sus = Sus.query.get(sus_id)
    form = SusDetailForm(request.form, obj=sus)
    if request.method == "POST":
        if form.validate():
            form.populate_obj(sus)
            db.session.commit()
            return redirect(url_for("sus.sus_detail", sus_id=sus.id))
    
    return render_template(
        'forms/model.jinja',
        form=form,
        type='edit',
        action=url_for('sus.sus_edit_detail', sus_id=sus.id))


@sus.route('/sus/take_test/<uuid:sus_uuid>/', methods=['GET', 'POST'])
def take_sus_test(sus_uuid):
    sus = Sus.query.filter(Sus.uuid == str(sus_uuid)).first()
    form = SusTestForm(request.form)
    if request.method == "POST":
        if form.validate():
            try:
                # We don't really want to require email ,
                # but we have to fake one for the user model
                user_uuid = uuid.uuid4()
                email = "{}@lobe.is".format(user_uuid)
                new_user = app.user_datastore.create_user(
                    name=form.data["name"],
                    email=email,
                    password=None,
                    uuid=user_uuid,
                    audio_setup=form.data["audio_setup"],
                    roles=[]
                )
                form.populate_obj(new_user)
                sus.add_participant(new_user)
                db.session.commit()
            except IntegrityError as e:
                print(e)
                app.logger.error(
                    "Could not create user for application," +
                    " email already in use")
                flash("Þetta netfang er nú þegar í notkun", category='error')
                return redirect(
                    url_for("sus.take_sus_test", sus_uuid=sus_uuid))
            return redirect(
                url_for("sus.sus_test", id=sus.id, uuid=new_user.uuid))

    return render_template(
        'take_sus_test.jinja',
        form=form,
        type='create',
        sus=sus,
        action=url_for('sus.take_sus_test', sus_uuid=sus_uuid))


@sus.route('/sus/sustest/<uuid:sus_uuid>/', methods=['GET'])
def sus_test(sus_uuid):
   
    sus = Sus.query.filter(Sus.uuid == str(sus_uuid)).first()
    sus_instances = SusObject.query.filter(SusObject.sus_id == sus.id)
    sus_list = [instance for instance in sus_instances if instance.path]
    #random.shuffle(sus_list)

    audio = []
    audio_url = []
    info = {'paths': [], 'texts': []}
    for i in sus_list:
        if i.custom_recording:
            audio.append(i.custom_recording)
            audio_url.append(i.custom_recording.get_download_url())
        else:
            continue
        info['paths'].append(i.path)
        info['texts'].append(i.text)
    audio_json = json.dumps([r.get_dict() for r in audio])
    sus_list_json = json.dumps([r.get_dict() for r in sus_list])

    return render_template(
        'sus_test.jinja',
        sus=sus,
        sus_list=sus_list,
        recordings=audio_json,
        recordings_url=audio_url,
        json_sus=sus_list_json,
        section='sus')




@sus.route('/sus/<int:sus_id>/sus_results/download', methods=['GET'])
@login_required
@organiser_of_sus_or_admin
def download_sus_data(sus_id):
    sus = Sus.query.get(sus_id)
    response_lines = [
        ";".join(map(str, line)) for line in sus.getResultData()
    ]
    csv = "\n".join(response_lines)
    filename = 'sus_results_{}_{}.csv'.format(sus.id, time.strftime("%Y-%m-%d-%H-%M-%S"))
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename={}".format(filename)})



@sus.route('/sus/stream_sus_demo')
@login_required
@roles_accepted('admin', 'organiser')
def stream_SUS_index_demo():
    other_dir = app.config["OTHER_DIR"]
    try:
        return send_from_directory(
            other_dir, 'synidaemi_sus_index.zip', as_attachment=True)
    except Exception as error:
        app.logger.error(
            "Error downloading a custom recording : {}\n{}".format(
                error, traceback.format_exc()))


@sus.route('/sus/<int:sus_id>/stream_zip')
@login_required
@organiser_of_sus_or_admin
def stream_SUS_zip(sus_id):
    sus = Sus.query.get(sus_id)
    sus_list = SusObject.query\
        .filter(SusObject.sus_id == sus_id)\
        .filter(SusObject.is_synth == False).order_by(
            resolve_order(
                SusObject,
                request.args.get('sort_by', default='id'),
                order=request.args.get('order', default='desc'))).all()

    results = 'sus_instance_id\tcustom_token_id\ttoken_text\n'
    for i in sus_list:
        results += "{}\t{}\t{}\n".format(
            str(i.id),
            str(i.custom_token.id),
            i.custom_token.text)

    generator = (cell for row in results for cell in row)

    return Response(
        generator,
        mimetype="text/plain",
        headers={
            "Content-Disposition":
            "attachment;filename={}_tokens.txt".format(
                sus.printable_id)}
        )


@sus.route('/sus/create', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'organiser')
def sus_create():
    try:
        sus = Sus()
        sus.uuid = uuid.uuid4()
        db.session.add(sus)
        db.session.commit()
        flash("Nýrri SUS prufu bætt við", category="success")
        return redirect(url_for('sus.sus_detail', sus_id=sus.id))
    except Exception as error:
        flash("Error creating SUS.", category="danger")
        app.logger.error("Error creating SUS {}\n{}".format(
            error, traceback.format_exc()))
    return redirect(url_for('sus.sus_list'))

@sus.route('/sus/instances/<int:sus_instance_id>/delete/', methods=['GET'])
@login_required
@organiser_of_sus_instance_or_admin
def delete_sus_instance(sus_instance_id):
    instance = SusObject.query.get(sus_instance_id)
    sus_id = instance.sus_id
    did_delete, errors = delete_sus_object_db(instance)
    if did_delete:
        flash("Línu var eytt", category='success')
    else:
        flash("Ekki gekk að eyða línu rétt", category='warning')
        print(errors)
    return redirect(url_for('sus.sus_detail', id=sus_id))


@sus.route('/custom-recording/<int:id>/download/')
def download_custom_recording(id):
    custom_recording = CustomRecording.query.get(id)
    try:
        return send_from_directory(
            custom_recording.get_directory(),
            custom_recording.fname,
            as_attachment=True)
    except Exception as error:
        flash("Error in finding recording.", category="warning")
        app.logger.error(
            "Error downloading a custom recording : {}\n{}".format(
                error, traceback.format_exc()))


@sus.route('/custom_tokens/<int:id>/')
@login_required
@roles_accepted('admin', 'Notandi')
def custom_token(id):
    return render_template(
        'custom_token.jinja',
        token=CustomToken.query.get(id),
        section='token')


@sus.route('/custom_tokens/<int:id>/download/')
@login_required
@roles_accepted('admin', 'Notandi')
def download_custom_token(id):
    token = CustomToken.query.get(id)
    try:
        return send_from_directory(
            token.get_directory(),
            token.fname,
            as_attachment=True)
    except Exception as error:
        app.logger.error(
            "Error downloading a token : {}\n{}".format(
                error, traceback.format_exc()))


@sus.route('/sus-done/<int:id>', methods=['GET'])
def sus_done(id):
    sus = Sus.query.get(id)
    return render_template("sus_done.jinja", sus=sus)
