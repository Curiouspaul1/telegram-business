from json import load
from flask import (
    Flask, request,
    redirect, session
)
from dotenv import load_dotenv
import requests
import os

load_dotenv()

# flask app instatnce
app = Flask(__name__)

# app config
app.config['SECRET_KEY'] = os.getenv('APP_SECRET')

# endpoints
@app.route("/<biz_name>", methods=['GET'])
def link(biz_name):
    session['biz_name'] = biz_name
    bot_url = "https://t.me/TG_businessBot"

    return redirect(bot_url)

# @app.route('/')

if __name__ == "__main__":
    app.run()

