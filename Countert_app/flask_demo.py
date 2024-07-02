from flask import Flask, render_template, request, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, db=0)

# Set the initial counter values if not set already
if not r.exists("likes"):
    likes = {str(i): 0 for i in range(1, 154)}
    r.hmset("likes", likes)

@app.route("/")
def index():
    counter = r.hgetall("likes")
    return render_template("choose_frogs.html", counters=counter)

@app.route("/incr", methods=["POST"])
def incr():
    try:
        # Log the incoming form data
        app.logger.info("Form data received: %s", request.form)
        img_id = int(request.form['image_id'])
        r.hincrby("likes", img_id, 1)
        count = r.hgetall("likes")
        likes = {int(k.decode()): int(v.decode()) for k, v in count.items()}
        return jsonify(success=True,likes=likes)
    except Exception as e:
        print(f"Error in incr route: {e}")
        return jsonify(success=False, error=str(e)), 500


if __name__ == "__main__":
    app.run(debug=True)









