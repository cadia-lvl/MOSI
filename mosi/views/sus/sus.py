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
@roles_accepted('admin')
def sus_list():
    page = int(request.args.get('page', 1))
    sus_list = Sus.query.order_by(
            resolve_order(
                Sus,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['MOS_PAGINATION'])
    return render_template(
        'sus_list.jinja',
        sus_list=sus_list,
        section='sus')



@sus.route('/sus/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def sus_detail(id):
    sus = Sus.query.get(id)
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
                        zip, zip_name, tsv_name, sus, id)
                    if successfully_uploaded and len(successfully_uploaded) > 0:
                        flash("Tókst að hlaða upp {} setningum.".format(
                            len(successfully_uploaded)),
                            category="success")
                    else:
                        flash(
                            "Ekki tókst að hlaða upp neinum setningum.",
                            category="warning")
                return redirect(url_for('sus.sus_detail', id=id))
            else:
                flash(
                    "Ekki tókst að hlaða inn skrá. Eingögnu hægt að hlaða inn skrám á stöðluðu formi.",
                    category="danger")
        else:
            flash(
                "Villa í formi, athugaðu að rétt sé fyllt inn og reyndu aftur.",
                category="danger")

    sus_list = SusObject.query.filter(SusObject.sus_id == id).order_by(
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


@sus.route('/sus/<int:id>/edit/detail', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def sus_edit_detail(id):
    sus = Sus.query.get(id)
    form = SusDetailForm(request.form, obj=sus)
    if request.method == "POST":
        if form.validate():
            form.populate_obj(sus)
            db.session.commit()
            return redirect(url_for("sus.sus_detail", id=sus.id))
    
    return render_template(
        'forms/model.jinja',
        form=form,
        type='edit',
        action=url_for('sus.sus_edit_detail', id=sus.id))


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


@sus.route('/sus/<int:id>/sustest/', methods=['GET'])
def sus_test(id):
   
    sus = Sus.query.get(id)
    sus_instances = SusObject.query.filter(SusObject.sus_id == id)
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


@sus.route('/sus/<int:id>/sus_results', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def sus_results(id):
    sus = Sus.query.get(id)
    sus_list = SusObject.query.filter(SusObject.sus_id == id).order_by(
            resolve_order(
                SusObject,
                request.args.get('sort_by', default='id'),
                order=request.args.get('order', default='desc'))).all()
    ratings = sus.getAllRatings()
    max_placement = 1
    for j in ratings:
        if j.placement > max_placement:
            max_placement = j.placement

    if len(ratings) == 0:
        return redirect(url_for('sus.sus_detail', id=sus.id))
    user_ids = sus.getAllUsers()
    users = User.query.filter(User.id.in_(user_ids)).all()

    all_rating_stats = []
    placement = [0]*max_placement
    p_counter = [0]*max_placement
    for i in ratings:
        all_rating_stats.append(i.rating)
        placement[i.placement - 1] += i.rating
        p_counter[i.placement - 1] += 1
    all_rating_stats = np.array(all_rating_stats)
    for i in range(len(placement)):
        if p_counter[i] != 0 and placement[i] != 0:
            placement[i] = placement[i]/p_counter[i]
    placement_info = {
        'placement': placement,
        'p_nums': list(range(1, len(sus_list)))}
    rating_json = {
        'average': round(np.mean(all_rating_stats), 2),
        'std': round(np.std(all_rating_stats), 2)}
    sus_stats = {
        'names': [],
        'means': [],
        'total_amount': []}
    for m in sus_list:
        sus_stats['names'].append(str(m.id))
        sus_stats['means'].append(m.average_rating)
        sus_stats['total_amount'].append(m.number_of_ratings)
    users_list = []
    users_graph_json = []
    for u in users:
        user_ratings = sus.getAllUserRatings(u.id)
        ratings_stats = []
        for r in user_ratings:
            ratings_stats.append(r.rating)
        ratings_stats = np.array(ratings_stats)

        sus_ratings_per_user = []
        for m in sus_list:
            if not m.getUserRating(u.id):
                sus_ratings_per_user.append('')
            else:
                sus_ratings_per_user.append(m.getUserRating(u.id))
        user_ratings = {
            "username": u.get_printable_name(),
            "ratings": sus_ratings_per_user}
        temp = {
            'user': u,
            'mean': round(np.mean(ratings_stats), 2),
            'std': round(np.std(ratings_stats), 2),
            'total': len(ratings_stats),
            'user_ratings': sus_ratings_per_user}
        temp2 = {
            'user_ratings': user_ratings}
        users_list.append(temp)
        users_graph_json.append(temp2)

    users_list = sorted(users_list, key=itemgetter('mean'))

    all_usernames_list = []
    user_name_dict = {}
    for u in users_graph_json:
        all_usernames_list.append(u['user_ratings']['username'])
        user_name_dict[u['user_ratings']['username']] = {'fullrating': u['user_ratings']['ratings']}
        indices = [i for i, x in enumerate(u['user_ratings']['ratings']) if x != '']
        user_name_dict[u['user_ratings']['username']]['selectiveRatings'] = [u['user_ratings']['ratings'][i] for i in indices]
        user_name_dict[u['user_ratings']['username']]['selectiveSusIds'] = [sus_stats['names'][i] for i in indices]
        user_name_dict[u['user_ratings']['username']]['selectiveSusMeans'] = [sus_stats['means'][i] for i in indices]

    # Average per voice index
    ratings_by_voice = sus.getResultsByVoice()
    per_voice_data = {
        "x": [],
        "y": [],
        "std": [],
    }
    for voice_idx, ratings in ratings_by_voice.items():
        per_voice_data["x"].append(voice_idx)
        per_voice_data["y"].append(round(np.mean([r.rating for r in ratings]), 2))
        per_voice_data["std"].append(round(np.std([r.rating for r in ratings]), 2))

    return render_template(
        'sus_results.jinja',
        sus=sus,
        sus_stats=sus_stats,
        ratings=ratings,
        placement_info=placement_info,
        all_usernames_list=all_usernames_list,
        user_name_dict=user_name_dict,
        users=users_list,
        rating_json=rating_json,
        users_graph_json=users_graph_json,
        per_voice_data=per_voice_data,
        sus_list=sus_list,
        section='sus'
    )


@sus.route('/sus/<int:id>/sus_results/download', methods=['GET'])
@login_required
@roles_accepted('admin')
def download_sus_data(id):
    sus = Sus.query.get(id)
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


@sus.route('/sus/<int:id>/stream_zip')
@login_required
@roles_accepted('admin')
def stream_SUS_zip(id):
    sus = Sus.query.get(id)
    sus_list = SusObject.query\
        .filter(SusObject.sus_id == id)\
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


@sus.route('/sus/stream_sus_demo')
@login_required
@roles_accepted('admin')
def stream_SUS_index_demo():
    other_dir = app.config["OTHER_DIR"]
    try:
        return send_from_directory(
            other_dir, 'synidaemi_sus_index.zip', as_attachment=True)
    except Exception as error:
        app.logger.error(
            "Error downloading a custom recording : {}\n{}".format(
                error, traceback.format_exc()))


@sus.route('/sus/post_sus_rating/<int:id>', methods=['POST'])
def post_sus_rating(id):
    sus_id = id
    try:
        sus_id = save_SUS_ratings(request.form, request.files)
    except Exception as error:
        flash(
            "Villa kom upp. Hafið samband við kerfisstjóra",
            category="danger")
        app.logger.error("Error posting recordings: {}\n{}".format(
            error, traceback.format_exc()))
        return Response(str(error), status=500)
    if sus_id is None:
        flash("Engar einkunnir í SUS prófi.", category='warning')
        return Response(url_for('sus.sus_list'), status=200)

    flash("SUS próf klárað", category='success')
    if current_user.is_anonymous:
        return Response(
            url_for('sus.sus_done', id=sus_id), status=200)
    else:
        return Response(
            url_for('sus.sus_detail', id=sus_id), status=200)


@sus.route('/sus/instances/<int:id>/edit', methods=['POST'])
@login_required
@roles_accepted('admin')
def sus_instance_edit(id):
    try:
        instance = SusObject.query.get(id)
        form = SusItemSelectionForm(request.form, obj=instance)
        form.populate_obj(instance)
        db.session.commit()
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        errorMessage = "<br>".join(list("{}: {}".format(
            key, ", ".join(value)) for key, value in form.errors.items()))
        return Response(errorMessage, status=500)


@sus.route('/sus/<int:id>/select_all', methods=['POST'])
@login_required
@roles_accepted('admin')
def sus_select_all(id):
    try:
        form = SusSelectAllForm(request.form)
        is_synth = True if form.data['is_synth'] == 'True' else False
        select = True if form.data['select'] == 'True' else False
        sus_list = SusObject.query\
            .filter(SusObject.sus_id == id)\
            .filter(SusObject.is_synth == is_synth).all()
        for m in sus_list:
            m.selected = select
        db.session.commit()
        return redirect(url_for('sus.sus_detail', id=id))
    except Exception as error:
        print(error)
        flash("Ekki gekk að merkja alla", category='warning')
    return redirect(url_for('sus.sus_detail', id=id))


@sus.route('/sus/instances/<int:id>/delete/', methods=['GET'])
@login_required
@roles_accepted('admin')
def delete_sus_instance(id):
    instance = SusObject.query.get(id)
    sus_id = instance.sus_id
    did_delete, errors = delete_sus_instance_db(instance)
    if did_delete:
        flash("Línu var eytt", category='success')
    else:
        flash("Ekki gekk að eyða línu rétt", category='warning')
        print(errors)
    return redirect(url_for('sus.sus_detail', id=sus_id))


@sus.route('/sus/create', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def sus_create():
    try:
        sus = Sus()
        sus.uuid = uuid.uuid4()
        db.session.add(sus)
        db.session.commit()
        flash("Nýrri SUS prufu bætt við", category="success")
        return redirect(url_for('sus.sus_detail', id=sus.id))
    except Exception as error:
        flash("Error creating SUS.", category="danger")
        app.logger.error("Error creating SUS {}\n{}".format(
            error, traceback.format_exc()))
    return redirect(url_for('sus.sus_list'))


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
