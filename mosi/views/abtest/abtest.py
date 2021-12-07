import json
from logging import error
import traceback
import random
import uuid
import numpy as np
from zipfile import ZipFile
from operator import add, itemgetter

from flask import (Blueprint, Response, send_from_directory, request,
                   render_template, flash, redirect, url_for)
from flask import current_app as app
from flask_security import login_required, roles_accepted, current_user
from sqlalchemy.exc import IntegrityError

from mosi.models import (ABInstance, User, ABtest, ABTuple,
                         CustomToken, CustomRecording, db)
from mosi.db import (resolve_order, save_custom_wav_for_abtest, delete_abtest_instance_db,
                        save_abtest_ratings, delete_abtest_tuple_db)
from mosi.forms import (ABtestSelectAllForm, ABtestUploadForm, ABtestItemSelectionForm,
                        ABtestTestForm, ABtestForm, ABtestDetailForm)

abtest = Blueprint(
    'abtest', __name__, template_folder='templates')


@abtest.route('/abtest/')
@login_required
@roles_accepted('admin')
def abtest_list():
    page = int(request.args.get('page', 1))
    abtest_list = ABtest.query.order_by(
            resolve_order(
                ABtest,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['MOS_PAGINATION'])
    return render_template(
        'abtest_list.jinja',
        abtest_list=abtest_list,
        section='abtest')


@abtest.route('/abtest/collection/none')
@login_required
@roles_accepted('admin')
def abtest_collection_none():
    page = int(request.args.get('page', 1))
    collection = json.dumps({'name': 'Óháð söfnun', 'id': 0})
    abtest_list = ABtest.query.filter(ABtest.collection_id == None).order_by(
            resolve_order(
                ABtest,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['MOS_PAGINATION'])
    return render_template(
        'abtest_no_collection_list.jinja',
        abtest_list=abtest_list,
        collection=collection,
        section='abtest')

@abtest.route('/abtest/create_tuple/<int:ab_id>/<int:first_id>/<int:second_id>/<int:ref_id>')
@abtest.route('/abtest/create_tuple/<int:ab_id>/<int:first_id>/<int:second_id>')
@login_required
@roles_accepted('admin')
def create_tuple(ab_id, first_id, second_id, ref_id=None):
    abtest = ABtest.query.get(ab_id)
    first = ABInstance.query.get(first_id)
    second = ABInstance.query.get(second_id)
    ref = ABInstance.query.get(ref_id) if ref_id else None
    abtuple = None

    if abtest and first and second:
        if first.abtest_id == abtest.id and second.abtest_id == abtest.id:
            if first.id != second.id:
                if ref and ref.id != first.id and ref.id != second.id and ref.abtest_id == abtest.id:
                    abtuple = ABTuple(abtest.id, first_id, second_id, ref_id)
                else:
                    abtuple = ABTuple(abtest.id, first_id, second_id, None)

    existing_tuple = ABTuple.query.filter(
        ABTuple.abtest_id == ab_id,
        ABTuple.ab_instance_first_id == first_id,
        ABTuple.ab_instance_second_id == second_id,
        ABTuple.ab_instance_referance_id == ref_id).first()

    if existing_tuple:
        flash("Ekki hægt að bæta við línu sem hefur verið bætt við áður", category='warning')

    elif abtuple:
        db.session.add(abtuple)
        db.session.commit()
        flash("Línu var bætt við", category='success')
    else:
        flash("Ekki gekk að bæta við línu", category='warning')
    response = {}
    return Response(json.dumps(response), status=200)
    #return redirect(url_for('abtest.abtest_detail', id=ab_id))
        
@abtest.route('/abtest/tuple/<int:id>/delete/', methods=['GET'])
@login_required
@roles_accepted('admin')
def delete_abtest_tuple(id):
    tuple = ABTuple.query.get(id)
    abtest_id = tuple.abtest_id
    did_delete, errors = delete_abtest_tuple_db(tuple)
    if did_delete:
        flash("Línu var eytt", category='success')
    else:
        flash("Ekki gekk að eyða línu rétt", category='warning')
        print(errors)
    return redirect(url_for('abtest.abtest_detail', id=abtest_id))

@abtest.route('/abtest/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def abtest_detail(id):
    abtest = ABtest.query.get(id)
    form = ABtestUploadForm()
    select_all_forms = [
        ABtestSelectAllForm(select=True),
        ABtestSelectAllForm(select=False)
    ]

    if request.method == 'POST':
        if form.validate():
            if(form.is_g2p.data):
                zip_file = request.files.get('files')
                with ZipFile(zip_file, 'r') as zip:
                    zip_name = zip_file.filename[:-4]
                    tsv_name = '{}/index.csv'.format(zip_name)
                    successfully_uploaded = save_custom_wav_for_abtest(
                        zip, zip_name, tsv_name, abtest, id)
                    if len(successfully_uploaded) > 0:
                        flash("Tókst að hlaða upp {} setningum.".format(
                            len(successfully_uploaded)),
                            category="success")
                    else:
                        flash(
                            "Ekki tókst að hlaða upp neinum setningum.",
                            category="warning")
                return redirect(url_for('abtest.abtest_detail', id=id))
            else:
                flash(
                    "Ekki tókst að hlaða inn skrá. Eingögnu hægt að hlaða inn skrám á stöðluðu formi.",
                    category="danger")
        else:
            flash(
                "Villa í formi, athugaðu að rétt sé fyllt inn og reyndu aftur.",
                category="danger")

    abtest_list = ABInstance.query.filter(ABInstance.abtest_id == id).order_by(
            resolve_order(
                ABInstance,
                request.args.get('sort_by', default='id'),
                order=request.args.get('order', default='desc'))).all()

    sentence_groups = {}
    for s in abtest_list:
        s_id = s.utterance_idx
        if s_id in sentence_groups:
            if s.text == sentence_groups[s_id]['info']['text']:
                sentence_groups[s_id]['instances'].append(s)
                if sentence_groups[s_id]['info']['has_reference'] == False and s.is_reference:
                    sentence_groups[s_id]['info']['has_reference'] = len(sentence_groups[s_id]['instances']) - 1
        else:
            sentence_groups[s_id] = {'info': {'has_reference': 0, 'text': s.text}, 'instances': [s]}
    ratings = abtest.getAllRatings()
    
    for key in sentence_groups:
        additional = []
        perms = [[a, b] for a in range(len(sentence_groups[key]["instances"])) for b in range(len(sentence_groups[key]["instances"]))[a + 1:]]
        sentence_groups[key]['info']['perms'] = perms
        
        if sentence_groups[key]['info']['has_reference']:
            for p in perms:
                ref_idx = sentence_groups[key]['info']['has_reference']
                if sentence_groups[key]['instances'][ref_idx] not in [sentence_groups[key]['instances'][p[0]], sentence_groups[key]['instances'][p[1]]]:
                    additional.append(p+[ref_idx])
        sentence_groups[key]['info']['perms'] = sentence_groups[key]['info']['perms'] + additional

    abtest_tuples = ABTuple.query.filter(ABTuple.abtest_id == id).all()
    
    for ab in abtest_tuples:
        ab.selection_form = ABtestItemSelectionForm(obj=ab)

    return render_template(
        'abtest.jinja',
        abtest=abtest,
        abtest_list=abtest_list,
        select_all_forms=select_all_forms,
        sentence_groups=sentence_groups,
        abtest_form=form,
        abtest_tuples=abtest_tuples,
        ratings=ratings,
        section='abtest')


@abtest.route('/abtest/<int:id>/edit/detail', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def abtest_edit_detail(id):
    abtest = ABtest.query.get(id)
    form = ABtestDetailForm(request.form, obj=abtest)
    if request.method == "POST":
        if form.validate():
            form.populate_obj(abtest)
            db.session.commit()
            return redirect(url_for("abtest.abtest_detail", id=abtest.id))
    
    form.show_text_in_test.data = abtest.show_text_in_test
    return render_template(
        'forms/model.jinja',
        form=form,
        type='edit',
        action=url_for('abtest.abtest_edit_detail', id=abtest.id))


@abtest.route('/abtest/take_test/<uuid:abtest_uuid>/', methods=['GET', 'POST'])
def take_abtest(abtest_uuid):
    abtest = ABtest.query.filter(ABtest.uuid == str(abtest_uuid)).first()
    form = ABtestTestForm(request.form)
    if request.method == "POST":
        if form.validate():
            try:
                # We don't really want to require email ,
                # but we have to fake one for the user model
                user_uuid = uuid.uuid4()
                email = "{}@mosi.is".format(user_uuid)
                new_user = app.user_datastore.create_user(
                    name=form.data["name"],
                    email=email,
                    password=None,
                    uuid=user_uuid,
                    audio_setup=form.data["audio_setup"],
                    roles=['ab_tester', 'test_partitipant']
                )
                form.populate_obj(new_user)
                abtest.add_participant(new_user)
                db.session.commit()
            except IntegrityError as e:
                print(e)
                app.logger.error(
                    "Could not create user for application," +
                    " email already in use")
                flash("Þetta netfang er nú þegar í notkun", category='error')
                return redirect(
                    url_for("abtest.take_abtest", abtest_uuid=abtest_uuid))
            return redirect(
                url_for("abtest.abtest_test", id=abtest.id, uuid=new_user.uuid))

    return render_template(
        'take_abtest.jinja',
        form=form,
        type='create',
        abtest=abtest,
        action=url_for('abtest.take_abtest', abtest_uuid=abtest_uuid))


@abtest.route('/abtest/<int:id>/abtest/<string:uuid>', methods=['GET', 'POST'])
def abtest_test(id, uuid):
    user = User.query.filter(User.uuid == uuid).first()
    if user.is_admin():
        if user.id != current_user.id:
            flash("Þú hefur ekki aðgang að þessari síðu", category='error')
            return redirect(url_for("abtest", id=id))
    abtest = ABtest.query.get(id)
    abtest_tuples = ABTuple.query.filter(ABTuple.abtest_id == id, ABTuple.selected == True)
    abtest_list = [tuple for tuple in abtest_tuples if tuple.first.path and tuple.second.path]
    random.shuffle(abtest_list)

    
    audio_data = []
    json_list = []
    for i in abtest_list:
        
        json_list_el = {}
        ab_tuple = {'first': {}, 'second': {}, 'tuple': i}
        ab_tuple['first']['recording'] = i.first.custom_recording
        ab_tuple['first']['url'] = i.first.custom_recording.get_download_url()
        ab_tuple['second']['recording'] = i.second.custom_recording
        ab_tuple['second']['url'] = i.second.custom_recording.get_download_url()
        json_list_el = {'tuple': i.get_dict(),'first': i.first.custom_recording.get_dict(), 'second':i.second.custom_recording.get_dict(), 'token': i.token.get_dict()}
        if i.has_reference:
            ab_tuple['reference'] = {'recording': i.ref.custom_recording}
            ab_tuple['reference']['url'] = i.ref.custom_recording.get_download_url()
            json_list_el['reference'] = i.ref.custom_recording.get_dict()
        audio_data.append(ab_tuple)
        json_list.append(json_list_el)
        
    audio_json = json.dumps(json_list)

    
    return render_template(
        'abtest_test.jinja',
        abtest=abtest,
        abtest_list=abtest_list,
        user=user,
        audio_data=audio_data,
        audio_json=audio_json,
        section='abtest')


@abtest.route('/abtest/<int:id>/abtest_results', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def abtest_results(id):
    abtest = ABtest.query.get(id)
    abtest_list = ABInstance.query.filter(ABInstance.abtest_id == id).order_by(
            resolve_order(
                ABInstance,
                request.args.get('sort_by', default='id'),
                order=request.args.get('order', default='desc'))).all()
    ratings = abtest.getAllRatings()
    max_placement = 1
    for j in ratings:
        if j.placement > max_placement:
            max_placement = j.placement

    if len(ratings) == 0:
        return redirect(url_for('abtest.abtest_detail', id=abtest.id))
    user_ids = abtest.getAllUsers()
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
        'p_nums': list(range(1, len(abtest_list)))}
    rating_json = {
        'average': round(np.mean(all_rating_stats), 2),
        'std': round(np.std(all_rating_stats), 2)}
    abtest_stats = {
        'names': [],
        'means': [],
        'total_amount': [],
        'picked': [],
        'not_picked': [],
        'ratio': [],
        'ratio_inverse': []}
    for m in abtest_list:
        ab_picked, ab_not_picked = m.ab_stats
        abtest_stats['names'].append(str(m.id))
        abtest_stats['means'].append(m.average_rating)
        abtest_stats['total_amount'].append(m.number_of_ratings)
        abtest_stats['picked'].append(ab_picked)
        abtest_stats['not_picked'].append(ab_not_picked)
        abtest_stats['ratio'].append(m.ab_ratio)
        abtest_stats['ratio_inverse'].append(m.ab_ratio_inverse)
    users_list = []
    users_graph_json = []
    for u in users:
        user_ratings = abtest.getAllUserRatings(u.id)
        ratings_stats = []
        for r in user_ratings:
            ratings_stats.append(r.rating)
        ratings_stats = np.array(ratings_stats)

        abtest_ratings_per_user = []
        for m in abtest_list:
            if not m.getUserRating(u.id):
                abtest_ratings_per_user.append('')
            else:
                abtest_ratings_per_user.append(m.getUserRating(u.id))
        user_ratings = {
            "username": u.get_printable_name(),
            "ratings": abtest_ratings_per_user}
        temp = {
            'user': u,
            'mean': round(np.mean(ratings_stats), 2),
            'std': round(np.std(ratings_stats), 2),
            'total': len(ratings_stats),
            'user_ratings': abtest_ratings_per_user}
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
        user_name_dict[u['user_ratings']['username']]['selectiveABtestIds'] = [abtest_stats['names'][i] for i in indices]
        user_name_dict[u['user_ratings']['username']]['selectiveABtestMeans'] = [abtest_stats['means'][i] for i in indices]

    # Average per voice index
    ratings_by_voice = abtest.getResultsByVoice()
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
        'abtest_results.jinja',
        abtest=abtest,
        abtest_stats=abtest_stats,
        ratings=ratings,
        placement_info=placement_info,
        all_usernames_list=all_usernames_list,
        user_name_dict=user_name_dict,
        users=users_list,
        rating_json=rating_json,
        users_graph_json=users_graph_json,
        per_voice_data=per_voice_data,
        abtest_list=abtest_list,
        section='abtest'
    )


@abtest.route('/abtest/<int:id>/abtest_results/download', methods=['GET'])
@login_required
@roles_accepted('admin')
def download_abtest_data(id):
    abtest = ABtest.query.get(id)
    response_lines = [
        ";".join(map(str, line)) for line in abtest.getResultData()
    ]
    csv = "\n".join(response_lines)
    filename = 'abtest_results_{}_{}.csv'.format(abtest.id, time.strftime("%Y-%m-%d-%H-%M-%S"))
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename={}".format(filename)})


@abtest.route('/abtest/<int:id>/stream_zip')
@login_required
@roles_accepted('admin')
def stream_abtest_zip(id):
    abtest = ABtest.query.get(id)
    abtest_list = ABInstance.query\
        .filter(ABInstance.abtest_id == id)\
        .filter(ABInstance.is_synth == False).order_by(
            resolve_order(
                ABInstance,
                request.args.get('sort_by', default='id'),
                order=request.args.get('order', default='desc'))).all()

    results = 'abtest_instance_id\tcustom_token_id\ttoken_text\n'
    for i in abtest_list:
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
                abtest.printable_id)}
        )


@abtest.route('/abtest/stream_abtest_demo')
@login_required
@roles_accepted('admin')
def stream_abtest_index_demo():
    other_dir = app.config["OTHER_DIR"]
    try:
        return send_from_directory(
            other_dir, 'synidaemi_abtest.zip', as_attachment=True)
    except Exception as error:
        app.logger.error(
            "Error downloading a custom recording : {}\n{}".format(
                error, traceback.format_exc()))


@abtest.route('/abtest/post_abtest_rating/<int:id>', methods=['POST'])
def post_abtest_rating(id):
    abtest_id = id
    try:
        abtest_id = save_abtest_ratings(request.form, request.files)
    except Exception as error:
        flash(
            "Villa kom upp. Hafið samband við kerfisstjóra",
            category="danger")
        app.logger.error("Error posting recordings: {}\n{}".format(
            error, traceback.format_exc()))
        return Response(str(error), status=500)
    if abtest_id is None:
        flash("Engar einkunnir í MOS prófi.", category='warning')
        return Response(url_for('abtest.abtest_list'), status=200)

    flash("AB próf klárað", category='success')
    if current_user.is_anonymous:
        return Response(
            url_for('abtest.abtest_done', id=abtest_id), status=200)
    else:
        return Response(
            url_for('abtest.abtest_detail', id=abtest_id), status=200)


@abtest.route('/abtest/tuple/<int:id>/edit', methods=['POST'])
@login_required
@roles_accepted('admin')
def abtest_tuple_edit(id):
    print('asdfasdf')
    try:
        tuple = ABTuple.query.get(id)
        form = ABtestItemSelectionForm(request.form, obj=tuple)
        form.populate_obj(tuple)
        db.session.commit()
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        errorMessage = "<br>".join(list("{}: {}".format(
            key, ", ".join(value)) for key, value in form.errors.items()))
        return Response(errorMessage, status=500)


@abtest.route('/abtest/<int:id>/select_all', methods=['POST'])
@login_required
@roles_accepted('admin')
def abtest_select_all(id):
    try:
        form = ABtestSelectAllForm(request.form)
        is_synth = True if form.data['is_synth'] == 'True' else False
        select = True if form.data['select'] == 'True' else False
        abtest_list = ABInstance.query\
            .filter(ABInstance.abtest_id == id)\
            .filter(ABInstance.is_synth == is_synth).all()
        for m in abtest_list:
            m.selected = select
        db.session.commit()
        return redirect(url_for('abtest.abtest_detail', id=id))
    except Exception as error:
        print(error)
        flash("Ekki gekk að merkja alla", category='warning')
    return redirect(url_for('abtest.abtest_detail', id=id))


@abtest.route('/abtest/instances/<int:id>/delete/', methods=['GET'])
@login_required
@roles_accepted('admin')
def delete_abtest_instance(id):
    instance = ABInstance.query.get(id)
    abtest_id = instance.abtest_id
    did_delete, errors = delete_abtest_instance_db(instance)
    if did_delete:
        flash("Línu var eytt", category='success')
    else:
        flash("Ekki gekk að eyða línu rétt", category='warning')
        print(errors)
    return redirect(url_for('abtest.abtest_detail', id=abtest_id))


@abtest.route('/abtest/create', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def abtest_create():
    try:
        abtest = ABtest()
        abtest.uuid = uuid.uuid4()
        db.session.add(abtest)
        db.session.commit()
        flash("Nýrri AB prufu bætt við", category="success")
        return redirect(url_for('abtest.abtest_detail', id=abtest.id))
    except Exception as error:
        flash("Error creating AB test.", category="danger")
        app.logger.error("Error creating MOS {}\n{}".format(
            error, traceback.format_exc()))
    return redirect(url_for('abtest.abtest_list'))



@abtest.route('/abtest-done/<int:id>', methods=['GET'])
def abtest_done(id):
    abtest = ABtest.query.get(id)
    return render_template("abtest_done.jinja", abtest=abtest)
