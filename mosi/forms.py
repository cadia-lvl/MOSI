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

from mosi.models import (Role, User, Mos, MosInstance, ABtest, ABInstance, ABTuple, db)


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



class ConfigurationForm(Form):
    name = TextField('Nafn stillinga')
    session_sz = IntegerField(
        'Fjöldi setninga í lotu',
        [
            validators.required(),
            validators.NumberRange(min=1, max=100)],
        default=50)
    live_transcribe = BooleanField(
        'Nota talgreini',
        description="Getur haft áhrif á hljóðgæði")
    visualize_mic = BooleanField(
        'Sýna hljóðnemaviðmót',
        description="Getur haft áhrif á hljóðgæði")
    analyze_sound = BooleanField("Sjálfvirk gæðastjórnun")
    auto_trim = BooleanField('Klippa hljóðbrot sjálfkrafa')
    channel_count = SelectField(
        "Fjöldi hljóðrása",
        choices=[(1, "1 rás"), (2, "2 rásir")],
        coerce=int,
        description='Athugið að hljóðrásir eru núna alltaf samþjappaðar' +
                    ' eftir upptökur.')
    sample_rate = SelectField(
        "Upptökutíðni",
        choices=[
            (16000, "16,000 Hz"),
            (32000, "32,000 Hz"),
            (44100, "44,100 Hz"),
            (48000, "48,000 Hz")],
        coerce=int)
    sample_size = SelectField(
        "Sýnisstærð",
        choices=[
            (16, "16 heiltölubitar"),
            (24, "24 heiltölubitar"),
            (32, "32 fleytibitar")],
        coerce=int,
        description='Ef PCM er valið sem hljóðmerkjamál er' +
                    'sýnisstærðin 32 bitar sjálfgefið')
    audio_codec = SelectField(
        "Hljóðmerkjamál",
        choices=[("pcm", "PCM")])
    trim_threshold = FloatField(
        "lágmarkshljóð (dB)",
        [validators.NumberRange(min=0)],
        default=40,
        description="Þröskuldur sem markar þögn, því lægri því meira telst " +
                    "sem þögn. Þetta kemur bara af notum þegar sjálfvirk " +
                    "klipping er notuð. Hljóðrófsritið er desíbel-skalað.")
    too_low_threshold = FloatField(
        "Lágmarkshljóð fyrir gæði (dB)",
        [validators.NumberRange(min=-100, max=0)],
        default=-15,
        description="Ef hljóðrófsrit upptöku fer aldrei yfir þennan " +
                    "þröskuld þá mun gæðastjórnunarkerfi merkja þessa " +
                    "upptöku of lága. Athugið að hér er hljóðrófsritið " +
                    "skalað eftir styrk.")
    too_high_threshold = FloatField(
        "Hámarkshljóð fyrir gæði (dB)",
        [validators.NumberRange(min=-100, max=0)],
        default=-4.5,
        description="Ef hljóðrófsrit upptöku fer yfir þennan þröskuld " +
                    "ákveðin fjölda af römmum í röð " +
                    "þá mun gæðastjórnunarkerfi merkja þessa upptöku of " +
                    "háa. Athugið að hér er hljóðrófsritið skalað eftir " +
                    "styrk.")
    too_high_frames = IntegerField(
        "Fjöldi of hárra ramma",
        [validators.NumberRange(min=0, max=100)],
        default=10,
        description="Segir til um hversu margir rammar i röð þurfa að " +
                    "vera fyrir ofan gæðastjórnunarþröskuldinn " +
                    "til að vera merkt sem of há upptaka.")
    auto_gain_control = BooleanField(
        "Sjálfvirk hljóðstýring",
        description="Getur haft áhrif á hljóðgæði")
    noise_suppression = BooleanField(
        "Dempun bakgrunnshljóðs",
        description="Getur haft áhrif á hljóðgæði")
    has_video = BooleanField(
        'Myndbandssöfnun',
        default=False)
    video_w = IntegerField(
        "Vídd myndbands í pixlum",
        [validators.NumberRange(min=0)],
        default=1280,
        description="Einungis notað ef söfnun er myndbandssöfnun.")
    video_h = IntegerField(
        "Hæð myndbands í pixlum",
        [validators.NumberRange(min=0)],
        default=720,
        description="Einungis notað ef söfnun er myndbandssöfnun.")
    video_codec = SelectField(
        "Myndmerkjamál",
        choices=[("vp8", "VP8")])


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
            'Fjöldi setnimmnga',
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
        "form_text": {
            "label": "Form texti", "widget": widgets.TextArea()
        },
        "help_text": {
            "label": "Hjálpartexti", "widget": widgets.TextArea()
        },
        "done_text": {
            "label": "Þakkartexti", "widget": widgets.TextArea()
        },
        "use_latin_square": {
            "label": "Nota latin-square"
        },
        "show_text_in_test": {
            "label": "Sýna texta við hljóðbút"
        },
    },
    only=["question", "form_text", "help_text",
          "done_text", "use_latin_square",
          "show_text_in_test"])


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
    is_synth = HiddenField()
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
        "show_text_in_test": {
            "label": "Sýna texta við hljóðbút"
        },
    },
    only=["question", "form_text", "help_text",
          "done_text", "use_latin_square",
          "show_text_in_test"])



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
