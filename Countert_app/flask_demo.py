from flask import Flask, render_template, request, jsonify, send_from_directory
import redis
import os
import csv
import datetime

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, db=0)

# Set the initial counter values if not set already
if not r.exists("likes"):
    likes = {str(i): 0 for i in range(1, 154)}
    r.hmset("likes", likes)

IMAGE_FOLDER = "Countert_app/static/frogs"
LOGGING_FOLDER = "results/"


@app.route("/")
def index():
    counter = r.hgetall("likes")
    return render_template("choose_frogs_refactor.html", counters=counter)


@app.route("/incr", methods=["POST"])
def incr():
    try:
        # Log the incoming form data
        app.logger.info("Form data received: %s", request.form)
        img_id = int(request.form["image_id"])
        r.hincrby("likes", img_id, 1)
        count = r.hgetall("likes")
        likes = {int(k.decode()): int(v.decode()) for k, v in count.items()}
        return jsonify(success=True, likes=likes)
    except Exception as e:
        print(f"Error in incr route: {e}")
        return jsonify(success=False, error=str(e)), 500


@app.route("/get_images", methods=["GET"])
def get_images():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")]
    # TODO fix this path so it is relative as well (and not hard-coded)
    image_urls = [f"/static/frogs/{image}" for image in images]
    return jsonify(image_urls)


# Serve images from the IMAGE_FOLDER
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)


@app.route("/log_selection", methods=["POST"])
def log_selection():
    data = request.json
    # Strip all folder and extension information to only retain the pure file name
    clicked_image = data.get("clicked_image").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    not_clicked_image = (
        data.get("not_clicked_image").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    )
    timestamp = data.get("timestamp")

    # Create a new CSV file if it does not exist
    # Make a new log file every minute
    log_file_name = f"logs_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    log_file_path = LOGGING_FOLDER + log_file_name

    if not os.path.exists(LOGGING_FOLDER):
        os.makedirs(LOGGING_FOLDER)

    if not os.path.exists(log_file_path):
        with open(log_file_path, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["clicked_image", "not_clicked_image", "timestamp"])

    with open(log_file_path, "a") as f:
        writer = csv.writer(f)
        writer.writerow([clicked_image, not_clicked_image, timestamp])

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)
