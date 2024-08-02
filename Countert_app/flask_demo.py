from flask import Flask, render_template, request, jsonify, send_from_directory
import redis
import os
import csv
import datetime

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, db=0)

IMAGE_FOLDER = "Countert_app/static/frogs"
LOGGING_FOLDER = "results/"
# By default, the app will log all incoming clicks.
# Change this to False if you want to disable click logging
LOG_CLICKS = True

# Create a vector containing all file names in the IMAGE_FOLDER
# These are treated as image IDs
image_files = [f.strip(".png") for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")]

# Set the initial counter values if not set already
if not r.exists("likes"):
    likes = {str(i): 0 for i in image_files}
    r.hset("likes", mapping=likes)


@app.route("/")
def index():
    return render_template("choose_frogs_refactor.html")


@app.route("/disable_logging")
def enable_click_test():
    LOG_CLICKS = False
    return jsonify({"status": "click logging disabled"})


@app.route("/enable_logging")
def enable_click_test():
    LOG_CLICKS = True
    return jsonify({"status": "click logging enabled"})


@app.route("/reset_counters", methods=["POST"])
def reset_counters():
    pipeline = r.pipeline()
    for i in image_files:
        pipeline.hset("likes", str(i), 0)
    pipeline.execute()
    return jsonify({"status": "success"})


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

    if LOG_CLICKS:
        # First, log the result to Redis to display in the Froschteich app
        r.hincrby("likes", clicked_image, 1)

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
