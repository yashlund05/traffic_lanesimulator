from flask import Flask, send_from_directory
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/")
def home():
    return '<link rel="stylesheet" href="/static/style.css"><h1>Hello CSS</h1>'

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

if __name__ == "__main__":
    print("STATIC FOLDER:", os.path.join(BASE_DIR, "static"))
    print("FILES IN STATIC:", os.listdir(os.path.join(BASE_DIR, "static")))
    app.run(debug=True)
