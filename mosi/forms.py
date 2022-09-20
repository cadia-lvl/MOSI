import os

from flask_security.forms import LoginForm, RegisterForm
from flask_wtf import RecaptchaField, FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (Form, HiddenField, MultipleFileField, SelectMultipleField,
                     SelectField, TextField, BooleanField, validators,
                     ValidationError, FloatField, widgets, StringField)
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired
from wtforms_alchemy import ModelForm
from wtforms_components import IntegerField

from mosi.models import (Role, User, Mos, MosInstance, ABtest, ABInstance, ABTuple, db, Sus, SusObject)


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class BulkTokenForm(Form):
    is_g2p = BooleanField(
        'G2P skjal.',
        description='Hakið við ef skjalið er G2P skjal samanber' +
                    ' lýsingu hér að ofan',
        default=False)
    files = MultipleFileField(
        'Textaskjöl',
        description='Veljið eitt eða fleiri textaskjöl.',
        validators=[validators.required()])

class ExtendedLoginForm(LoginForm):
    if not os.getenv("FLASK_ENV", 'development') == 'development':
        recaptcha = RecaptchaField()


class ExtendedRegisterForm(RegisterForm):
    name = TextField(
        'Nafn',
        [validators.required()])
    sex = SelectField(
        'Kyn',
        [validators.required()],
        choices=[
            ('Kona', 'Kona'),
            ('Karl', 'Karl'),
            ('Annað', 'Annað')])
    dialect = SelectField(
        'Framburður',
        [validators.required()],
        choices=[
            ('Linmæli', 'Linmæli'),
            ('Harðmæli', 'Harðmæli'),
            ('Raddaður framburður', 'Raddaður framburður'),
            ('hv-framburður', 'hv-framburður'),
            ('bð-, gð-framburður', 'bð-, gð-framburður'),
            ('ngl-framburður', 'ngl-framburður'),
            ('rn-, rl-framburður', 'rn-, rl-framburður'),
            ('Vestfirskur einhljóðaframburður',
                'Vestfirskur einhljóðaframburður'),
            ('Skaftfellskur einhljóðaframburður',
                'Skaftfellskur einhljóðaframburður')])
    age = IntegerField(
        'Aldur',
        [
            validators.required(),
            validators.NumberRange(min=18, max=100)])
    is_admin = BooleanField("Notandi er vefstjóri")


class VerifierRegisterForm(RegisterForm):
    name = TextField(
        'Nafn',
        [validators.required()])
    

class OrganiserRegisterForm(RegisterForm):
    name = TextField(
        'Nafn',
        [validators.required()])


class UserEditForm(Form):
    name = TextField('Nafn')
    email = TextField('Netfang')
    dialect = SelectField(
        'Framburður',
        [validators.required()],
        choices=[
            ('Linmæli', 'Linmæli'),
            ('Harðmæli', 'Harðmæli'),
            ('Raddaður framburður', 'Raddaður framburður'),
            ('hv-framburður', 'hv-framburður'),
            ('bð-, gð-framburður', 'bð-, gð-framburður'),
            ('ngl-framburður', 'ngl-framburður'),
            ('rn-, rl-framburður', 'rn-, rl-framburður'),
            ('Vestfirskur einhljóðaframburður',
                'Vestfirskur einhljóðaframburður'),
            ('Skaftfellskur einhljóðaframburður',
                'Skaftfellskur einhljóðaframburður')])
    sex = SelectField(
        'Kyn',
        [validators.required()],
        choices=[
            ('Kona', 'Kona'),
            ('Karl', 'Karl'),
            ('Annað', 'Annað')])
    age = IntegerField('Aldur')
    active = BooleanField("Virkur")




RoleForm = model_form(
    model=Role,
    base_class=Form,
    db_session=db.session)


class ApplicationForm(Form):
    name = StringField(
        "Nafn",
        [validators.required()])
    sex = SelectField(
        "Kyn",
        [validators.required()],
        choices=[
            ('Kona', 'Kona'),
            ('Karl', 'Karl'),
            ('Annað', 'Annað')])
    age = IntegerField(
        "Aldur",
        [
            validators.required(),
            validators.NumberRange(min=10, max=120)])
    voice = SelectField(
        "Rödd",
        [validators.required()],
        choices=[
            ("sopran", "Sópran"),
            ("alt", "Alt"),
            ("tenor", "Tenór"),
            ("bassi", "Bassi"),
        ])
    email = EmailField(
        "Netfang",
        [validators.required()])
    phone = StringField("Sími")
    terms_agreement = BooleanField(
        "Ég samþykki <a href='/tos/' target='_blank'>skilmála" +
        "og gagnastefnu LVL</a>",
        validators=[InputRequired()])


class MosForm(ModelForm):
    class Meta:
        model = Mos
        exclude = ['uuid']
        num_samples = IntegerField(
            'Fjöldi setninga',
            [validators.required()])

    def __init__(self, max_available, *args, **kwargs):
        super(MosForm, self).__init__(*args, **kwargs)
        self.max_available = max_available

    def validate_num_samples(form, field):
        if field.data >= form.max_available or field.data < 0:
            raise ValidationError(
                "Ekki nógu markar upptökur til í safni. Sláðu inn tölu" +
                "á milli 0 og {}".format(form.max_available))


class MosSelectAllForm(Form):
    is_synth = HiddenField()
    select = HiddenField()


MosDetailForm = model_form(
    Mos,
    db_session=db.session,
    field_args={
        "question": {
            "label": "Spurning",
        },
        "display_name": {
            "label": "Nafn á prófi",
        },
        "form_text": {
            "label": "Form texti", "widget": widgets.TextArea()
        },
        "help_text": {
            "label": "Hjálpartexti", "widget": widgets.TextArea()
        },
        "done_text": {
            "label": "Þakkartexti", "widget": widgets.TextArea()
        },
        "num_samples": {
            "label": "Fjöldi setninga", "widget": widgets.html5.NumberInput(min=0, max=90)
        },
        "use_latin_square": {
            "label": "Nota latin-square"
        },
        "show_text_in_test": {
            "label": "Sýna texta við hljóðbút"
        },
    },
    only=["question", "form_text", "help_text",
          "done_text", "use_latin_square", "num_samples",
          "show_text_in_test", 'display_name'])


class MosItemSelectionForm(ModelForm):
    class Meta:
        model = MosInstance
        exclude = ['is_synth']


class MosTestForm(Form):
    name = StringField("Nafn", [validators.required()])
    age = IntegerField("Aldur", [validators.required(),
                       validators.NumberRange(min=10, max=120)])
    audio_setup = StringField("Hvers konar heyrnatól/hátalara ertu með?", [validators.required()])




class MosUploadForm(FlaskForm):
    is_g2p = BooleanField(
        'Staðlað form.',
        description='Hakið við ef skráin er á stöðluðu formi' +
                    ' samanber lýsingu hér að ofan',
        default=False)
    files = FileField(
        validators=[
            FileAllowed(['zip'], 'Skrá verður að vera zip mappa'),
            FileRequired('Hladdu upp zip skrá')])



class ABtestForm(ModelForm):
    class Meta:
        model = ABtest
        exclude = ['uuid']
        num_samples = IntegerField(
            'Fjöldi setnimmnga',
            [validators.required()])

    def __init__(self, max_available, *args, **kwargs):
        super(ABtestForm, self).__init__(*args, **kwargs)
        self.max_available = max_available

    def validate_num_samples(form, field):
        if field.data >= form.max_available or field.data < 0:
            raise ValidationError(
                "Ekki nógu markar upptökur til í safni. Sláðu inn tölu" +
                "á milli 0 og {}".format(form.max_available))


class ABtestSelectAllForm(Form):
    select = HiddenField()


ABtestDetailForm = model_form(
    ABtest,
    db_session=db.session,
    field_args={
        "question": {
            "label": "Spurning",
        },
        "form_text": {
            "label": "Form texti", "widget": widgets.TextArea()
        },
        "help_text": {
            "label": "Hjálpartexti", "widget": widgets.TextArea()
        },
        "done_text": {
            "label": "Þakkartexti", "widget": widgets.TextArea()
        },
        "num_listening_samples_per_test": {
            "label": "Hámark setninga sem þáttakendur hlusta á", "widget": widgets.html5.NumberInput(step=None, min=1, max=1000)
        },
        "show_text_in_test": {
            "label": "Sýna texta við hljóðbút"
        },

    },
    only=["question", "form_text", "help_text",
          "done_text", "use_latin_square", "num_listening_samples_per_test",
          "show_text_in_test"])

SusDetailForm = model_form(
    Sus,
    db_session=db.session,
    field_args={
        "question": {
            "label": "Spurning",
        },
        "form_text": {
            "label": "Form texti", "widget": widgets.TextArea()
        },
        "help_text": {
            "label": "Hjálpartexti", "widget": widgets.TextArea()
        },
        "done_text": {
            "label": "Þakkartexti", "widget": widgets.TextArea()
        },
        "max_listens": {
            "label": "Fjöldi hlustana", "widget": widgets.html5.NumberInput(step=1, min=1)
        },
    },
    only=["question", "form_text", "help_text",
          "done_text", "use_latin_square", "max_listens"])


class ABtestTestForm(Form):
    name = StringField("Nafn", [validators.required()])
    age = IntegerField("Aldur", [validators.required(),
                       validators.NumberRange(min=10, max=120)])
    audio_setup = StringField("Hvers konar heyrnatól/hátalara ertu með?", [validators.required()])


class ABtestItemSelectionForm(ModelForm):
    class Meta:
        model = ABTuple
        exclude = []


class ABtestUploadForm(FlaskForm):
    is_g2p = BooleanField(
        'Staðlað form.',
        description='Hakið við ef skráin er á stöðluðu formi' +
                    ' samanber lýsingu hér að ofan',
        default=False)
    files = FileField(
        validators=[
            FileAllowed(['zip'], 'Skrá verður að vera zip mappa'),
            FileRequired('Hladdu upp zip skrá')])


class SusUploadForm(FlaskForm):
    is_g2p = BooleanField(
        'Staðlað form.',
        description='Hakið við ef skráin er á stöðluðu formi' +
                    ' samanber lýsingu hér að ofan',
        default=False)
    files = FileField(
        validators=[
            FileAllowed(['zip'], 'Skrá verður að vera zip mappa'),
            FileRequired('Hladdu upp zip skrá')])

class SusSelectAllForm(Form):
    select = HiddenField()

class SusItemSelectionForm(ModelForm):
    class Meta:
        model = SusObject

class SusTestForm(Form):
    name = StringField("Nafn", [validators.required()])
    age = IntegerField("Aldur", [validators.required(),
                       validators.NumberRange(min=10, max=120)])
    audio_setup = StringField("Hvers konar heyrnatól/hátalara ertu með?", [validators.required()])