from flask import Blueprint, render_template

documents = Blueprint('documents', __name__, template_folder='documents')

@documents.route('/get-api-key')
def get_api_key():
    return render_template("get_api_key.html")