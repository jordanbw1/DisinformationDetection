from flask import Flask, render_template, request, send_from_directory
from web_detect import run_prompt
import threading

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        email = request.form['email']
        # TODO: Regex to confirm email is in email format. Reject if not.

        # Create a thread and pass the function to it
        thread = threading.Thread(target=run_prompt, args=(prompt,email,))

        # Start the thread
        thread.start()
        
    # TODO: Render a page that tells the user the thing is running, and that we will get back to them with an email when done.
    return render_template('index.html')

# Define the route for downloading files
@app.route('/download/<path:filename>',  methods=['GET'])
def download(filename):
    # Send the file to the user
    return send_from_directory("dynamic/prompt_results", filename)

if __name__ == '__main__':
    app.run(debug=True)
