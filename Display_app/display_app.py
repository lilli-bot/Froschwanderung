from flask import Flask, render_template, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, db=0)


@app.route("/")
def index():
    counters = r.hgetall("likes")
    counters = {k.decode("utf-8"): int(v) for k, v in counters.items()}
    return render_template("allfrogs.html", counters=counters)


@app.route("/get_counters")
def get_counters():
    counters = r.hgetall("likes")
    counters = {k.decode("utf-8"): int(v) for k, v in counters.items()}
    return jsonify(counters=counters)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
