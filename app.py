from flask import Flask, request


app = Flask(__name__)


VERIFY_TOKEN = "EAATMA90XnhUBPxFkQlWPgIQSHJkEoZBZAbrMArObKYP0Hn5a6w0PhliUCD1sJqOSbYIb4ujUIMysDh2NCb4Fzx5bjRusxBMFQDbtG6ZCBOzztIsxDzXpqqjqGzNufZCIv0AyznbSgjiSGgDIyRXogsYlKPHYygzi2xtZAitDXzFJbF3JTPs0UW55ZCYhv3FwjZB6pySROLVqRk9CJvKZBYaRRpfFzG1cZAWfqe71wqZBx3VIujlVaIZATbUpBdRjm5bZC2BiSXUvCgedg3cz9qBZCZAgZDZD"


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verificación inicial de Meta
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    if request.method == "POST":
        # Mensajes entrantes desde WhatsApp
        data = request.get_json()
        print(data)
        return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(port=5000)
