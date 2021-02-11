# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Forms for user profiles."""

from __future__ import absolute_import, print_function

from flask import current_app
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from flask_security.forms import email_required, email_validator, \
    unique_user_email
from flask_wtf import FlaskForm
from sqlalchemy.orm.exc import NoResultFound
from wtforms import BooleanField, FormField, StringField, SubmitField, \
    SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, EqualTo, Optional, \
    StopValidation, ValidationError, Regexp
from wtforms_components import read_only

from .api import current_userprofile
from .models import UserProfile
from .validators import USERNAME_RULES, validate_username


def strip_filter(text):
    """Filter for trimming whitespace.

    :param text: The text to strip.
    :returns: The stripped text.
    """
    return text.strip() if text else text


def current_user_email(form, field):
    """Field validator to stop validation if email wasn't changed."""
    if current_user.email == field.data:
        raise StopValidation()

class ProfileForm(FlaskForm):
    """Form for editing user profile."""

    username = StringField(
        # NOTE: Form field label
        _('Username'),
        # NOTE: Form field help text
        description=_('Required. %(username_rules)s',
                      username_rules=USERNAME_RULES),
        validators=[DataRequired(message=_('Username not provided.'))],
        filters=[strip_filter])

    last_name = StringField(
        # NOTE: Form label
        _('Last name'),
        filters=[strip_filter])

    first_name = StringField(
        # NOTE: Form label
        _('First name'),
        filters=[strip_filter])

    birth_date = DateField(
        _('Birth Date'),
        format='%Y-%m-%d',
        validators=(Optional(),))

    street = StringField(
        # NOTE: Form label
        _('Street'),
        filters=[strip_filter], )

    postal_code = StringField(
        # NOTE: Form label
        _('Postal Code'),
        filters=[strip_filter], )

    city = StringField(
        # NOTE: Form label
        _('City'),
        filters=[strip_filter])

    home_phone = StringField(
        # NOTE: Form label
        _('Home phone number'),
        filters=[strip_filter],
        validators=[
            Regexp(r'^\+[0-9]*$|^$', message=_("Phone number with the international prefix, without spaces, ie +41221234567.")),
        ])

    business_phone = StringField(
        # NOTE: Form label
        _('Business phone number'),
        filters=[strip_filter],
        validators=[
            Regexp(r'^\+[0-9]*$|^$', message=_("Phone number with the international prefix, without spaces, ie +41221234567.")),
        ])

    mobile_phone = StringField(
        # NOTE: Form label
        _('Mobile phone number'),
        filters=[strip_filter],
        validators=[
            Regexp(r'^\+[0-9]*$|^$', message=_("Phone number with the international prefix, without spaces, ie +41221234567.")),
        ])

    other_phone = StringField(
        # NOTE: Form label
        _('Other phone number'),
        filters=[strip_filter],
        validators=[
            Regexp(r'^\+[0-9]*$|^$', message=_("Phone number with the international prefix, without spaces, ie +41221234567.")),
        ])

    gender = SelectField(
        _('Gender'),
        choices=[
            ('male', _('male')),
            ('female', _('female')),
            ('other', _('other'))]
    )

    country = SelectField(
        _('Country'),
        choices=[]
    )

    keep_history = BooleanField(
        # NOTE: Form label
        _('Keep History'),
        validators=[],
        description=_('If enabled the loan history is saved for a maximum of six months. It is visible to you and the library staff.'))

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        # read only fields
        get_readonly_fields = current_app.config.get(
            'USERPROFILES_READONLY_FIELDS', [])
        for field in get_readonly_fields():
            read_only(getattr(self, field))
        get_countries = current_app.config.get('USERPROFILES_COUNTRIES')
        if get_countries:
            self.country.choices = get_countries()


    def validate_username(form, field):
        """Wrap username validator for WTForms."""
        try:
            validate_username(field.data)
        except ValueError as e:
            raise ValidationError(e)

        try:
            user_profile = UserProfile.get_by_username(field.data)
            if current_userprofile.is_anonymous or \
                    (current_userprofile.user_id != user_profile.user_id and
                     field.data != current_userprofile.username):
                # NOTE: Form validation error.
                raise ValidationError(_('Username already exists.'))
        except NoResultFound:
            return


class EmailProfileForm(ProfileForm):
    """Form to allow editing of email address."""

    email = StringField(
        # NOTE: Form field label
        _('Email address'),
        filters=[lambda x: x.lower() if x is not None else x, ],
        validators=[
            Optional(),
            current_user_email,
            email_validator,
            unique_user_email,
        ],
    )

    email_repeat = StringField(
        # NOTE: Form field label
        _('Re-enter email address'),
        # NOTE: Form field help text
        description=_('Please re-enter your email address.'),
        filters=[lambda x: x.lower() if x else x, ],
        validators=[
            Optional(),
            # NOTE: Form validation error.
            EqualTo('email', message=_('Email addresses do not match.'))
        ]
    )


class VerificationForm(FlaskForm):
    """Form to render a button to request email confirmation."""

    # NOTE: Form button label
    send_verification_email = SubmitField(_('Resend verification email'))


def register_form_factory(Form):
    """Factory for creating an extended user registration form."""
    class CsrfDisabledProfileForm(ProfileForm):
        """Subclass of ProfileForm to disable CSRF token in the inner form.

        This class will always be a inner form field of the parent class
        `Form`. The parent will add/remove the CSRF token in the form.
        """

        def __init__(self, *args, **kwargs):
            """Initialize the object by hardcoding CSRF token to false."""
            kwargs = _update_with_csrf_disabled(kwargs)
            super(CsrfDisabledProfileForm, self).__init__(*args, **kwargs)

    class RegisterForm(Form):
        """RegisterForm extended with UserProfile details."""

        profile = FormField(CsrfDisabledProfileForm, separator='.')

    return RegisterForm


def confirm_register_form_factory(Form):
    """Factory for creating a confirm register form."""
    class CsrfDisabledProfileForm(ProfileForm):
        """Subclass of ProfileForm to disable CSRF token in the inner form.

        This class will always be a inner form field of the parent class
        `Form`. The parent will add/remove the CSRF token in the form.
        """

        def __init__(self, *args, **kwargs):
            """Initialize the object by hardcoding CSRF token to false."""
            kwargs = _update_with_csrf_disabled(kwargs)
            super(CsrfDisabledProfileForm, self).__init__(*args, **kwargs)

    class ConfirmRegisterForm(Form):
        """RegisterForm extended with UserProfile details."""

        profile = FormField(CsrfDisabledProfileForm, separator='.')

    return ConfirmRegisterForm


def _update_with_csrf_disabled(d=None):
    """Update the input dict with CSRF disabled depending on WTF-Form version.

    From Flask-WTF 0.14.0, `csrf_enabled` param has been deprecated in favor of
    `meta={csrf: True/False}`.
    """
    if d is None:
        d = {}

    import flask_wtf
    from pkg_resources import parse_version
    supports_meta = parse_version(flask_wtf.__version__) >= parse_version(
        "0.14.0")
    if supports_meta:
        d.setdefault('meta', {})
        d['meta'].update({'csrf': False})
    else:
        d['csrf_enabled'] = False
    return d
