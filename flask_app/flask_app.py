from flask import Flask, render_template, request, jsonify, send_from_directory
import redis
import os
import csv
import datetime
import pytz
import uuid

LOG_CLICKS = True


def create_app(redis_client=None):
    app = Flask(__name__)
    app.redis_client = (
        redis_client if redis_client else redis.Redis(host="localhost", port=6379, db=0)
    )
    r = app.redis_client

    IMAGE_FOLDER = "flask_app/static/frogs"
    LOGGING_FOLDER = "results/"
    # By default, the app will log all incoming clicks.
    # Change this to False if you want to disable click logging
    LOG_CLICKS = True

    # Create a vector containing all file names in the IMAGE_FOLDER
    # These are treated as image IDs
    image_files = [
        f.strip(".png") for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")
    ]

    # Set the initial counter values if not set already
    if not r.exists("likes"):
        likes = {str(i): 0 for i in image_files}
        r.hset("likes", mapping=likes)

    @app.route("/")
    def index():
        return render_template("choose_frogs_refactor.html")

    @app.route("/disable_logging", methods=["POST"])
    def disable_logging():
        global LOG_CLICKS
        LOG_CLICKS = False
        return jsonify({"status": "click logging disabled"})

    @app.route("/enable_logging", methods=["POST"])
    def enable_logging():
        global LOG_CLICKS
        LOG_CLICKS = True
        return jsonify({"status": "click logging enabled"})

    @app.route("/logging_status", methods=["POST"])
    def logging_status():
        global LOG_CLICKS
        status = "enabled" if LOG_CLICKS else "disabled"
        return jsonify({"status": f"logging is {status}"})

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
        timestamp = datetime.datetime.fromisoformat(data.get("timestamp")).astimezone(
            pytz.timezone("Europe/Berlin")
        )
        event_id = uuid.uuid4()

        if LOG_CLICKS:
            # First, log the result to Redis to display in the Froschteich app
            r.hincrby("likes", clicked_image, 1)

            # Create a new CSV file if it does not exist
            # Make a new log file every minute
            log_file_name = (
                f"logs_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
            )
            log_file_path = LOGGING_FOLDER + log_file_name

            if not os.path.exists(LOGGING_FOLDER):
                os.makedirs(LOGGING_FOLDER)

            if not os.path.exists(log_file_path):
                with open(log_file_path, "w") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["event_id", "clicked_image", "not_clicked_image", "timestamp"]
                    )

            with open(log_file_path, "a") as f:
                writer = csv.writer(f)
                writer.writerow([event_id, clicked_image, not_clicked_image, timestamp])

        return jsonify({"status": "success"}), 200

    @app.route("/froschteich")
    def froschteich():
        # TODO set up config file to synchronise name of Redis table across apps
        counters = r.hgetall("likes")
        counters = {k.decode("utf-8"): int(v) for k, v in counters.items()}
        return render_template("allfrogs.html", counters=counters)

    @app.route("/get_counters")
    def get_counters():
        counters = r.hgetall("likes")
        counters = {k.decode("utf-8"): int(v) for k, v in counters.items()}
        return jsonify(counters=counters)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
