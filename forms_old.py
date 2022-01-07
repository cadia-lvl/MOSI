import os

from flask import current_app as app
from flask import url_for
from flask_security.forms import LoginForm, RegisterForm
from flask_wtf import RecaptchaField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (Form, HiddenField, MultipleFileField, SelectMultipleField,
                     SelectField, TextField, IntegerField, BooleanField,
                     validators, ValidationError, FloatField, widgets, StringField, RadioField)

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired
from wtforms_alchemy import ModelForm
from wtforms_components import ColorField

from models import (
    Collection, Configuration, Role, User,
    VerifierIcon, PremiumItem, VerifierQuote, VerifierTitle,
    VerifierFont, db, Posting, Application, Mos, MosInstance)



# TODO: move to app configuration
sex_choices = [('Kona','Kona'), ('Karl','Karl'), ('Annað','Annað')]
dialect_choices = [
    ('Linmæli', 'Linmæli'),
    ('Harðmæli', 'Harðmæli'),
    ('Raddaður framburður', 'Raddaður framburður'),
    ('hv-framburður', 'hv-framburður'),
    ('bð-, gð-framburður', 'bð-, gð-framburður'),
    ('ngl-framburður', 'ngl-framburður'),
    ('rn-, rl-framburður', 'rn-, rl-framburður'),
    ('Vestfirskur einhljóðaframburður', 'Vestfirskur einhljóðaframburður'),
    ('Skaftfellskur einhljóðaframburður', 'Skaftfellskur einhljóðaframburður')
]
voice_choices = [
    ("sopran", "Sópran"),
    ("alt", "Alt"),
    ("tenor", "Tenór"),
    ("bassi", "Bassi"),
]


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MosForm(ModelForm):

    class Meta:
        model = Mos
        exclude = ['uuid']
        num_samples = IntegerField('Fjöldi setninga', [validators.required()])
    
    def __init__(self, max_available, *args, **kwargs):
        super(MosForm, self).__init__(*args, **kwargs)
        self.max_available = max_available
    
    def validate_num_samples(form, field):
        if field.data >= form.max_available or field.data < 0:
            raise ValidationError("Ekki nógu markar upptökur til í safni. Sláðu inn tölu á milli 0 og {}".format(form.max_available))


class MosSelectAllForm(Form):
    is_synth = HiddenField()
    select = HiddenField()


class MosItemSelectionForm(ModelForm):
    class Meta:
        model = MosInstance
        exclude = ['is_synth']

class MosTestForm(Form):
    name = StringField("Nafn", [validators.required()])
    age = IntegerField("Aldur", [validators.required(),
                       validators.NumberRange(min=10, max=120)])
    email = EmailField("Netfang", [validators.required()])


class MosUploadForm(FlaskForm):
    is_g2p = BooleanField('Staðlað form.', description='Hakið við ef uphleðslan er á stöðluðu formi samanber lýsingu hér að ofan',
                          default=False)
    files = FileField(validators=[FileAllowed(['zip'], 'Skrá verður að vera zip mappa'), FileRequired('Hladdu upp zip skrá')])


class ExtendedLoginForm(LoginForm):
    if not os.getenv("FLASK_ENV", 'development') == 'development':
        recaptcha = RecaptchaField()


class ExtendedRegisterForm(RegisterForm):
    name = TextField('Nafn', [validators.required()])
    sex = SelectField('Kyn',
                      [validators.required()], choices=sex_choices)
    dialect = SelectField('Framburður', [validators.required()],
                          choices=dialect_choices)
    age = IntegerField('Aldur', [validators.required(),
                                 validators.NumberRange(min=18, max=100)])
    is_admin = BooleanField("Notandi er vefstjóri")



class UserEditForm(Form):
    name = TextField('Nafn')
    email = TextField('Netfang')
    dialect = SelectField('Framburður', [validators.required()],
                          choices=dialect_choices)
    sex = SelectField('Kyn',
                      [validators.required()], choices=sex_choices)
    age = IntegerField('Aldur')



class _TermsLazyLabel(object):
    """
    Lazy loadable label for the terms and agreements check field.
    Since app context is not available when forms are imported
    we need to lazy load the label.
    """
    def __repr__(self):
        return f'Ég samþykki <a href="{url_for("tos")}" target="_blank">skilmála og gagnastefnu LVL</a>'


class SusUploadForm(FlaskForm):
    is_g2p = BooleanField('Staðlað form.', description='Hakið við ef uphleðslan er á stöðluðu formi samanber lýsingu hér að ofan',
                          default=False)
    files = FileField(validators=[FileAllowed(['zip'], 'Skrá verður að vera zip mappa'), FileRequired('Hladdu upp zip skrá')])
