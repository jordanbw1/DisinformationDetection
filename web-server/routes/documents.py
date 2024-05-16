from flask import Blueprint, render_template

documents_routes = Blueprint('documents', __name__, template_folder='documents')

@documents_routes.route('/get-gemini-key')
def get_gemini_key():
    return render_template("get_gemini_key.html")

@documents_routes.route('/get-chatgpt-key')
def get_chatgpt_key():
    return render_template("get_chatgpt_key.html")