from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired, Length

class LandingPageForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(1, 500)])
    banner_image = FileField('Banner Image', validators=[DataRequired()])
    submit = SubmitField('Continue')