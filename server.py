from flask import (
    Flask, request,
    redirect
)
import requests

# flask app instatnce
app = Flask(__name__)

# endpoints
@app.route("/<biz_name>", methods=['POST'])
def link(biz_name):
    bot_url = "https://t.me/TG_businessBot"
    return redirect(bot_url)


if __name__ == "__main__":
    app.run()
