# Froschwanderung

Interactive [Frog] Ranking Game

## Idea and Purpose

## How to Use?

### Prerequisites

This repository assumes you have Python > 3.9, homebrew and Docker, as well as Docker Compose installed on your machine.

### Installation

The `make install` command needs to be executed once after you have cloned this repository to your local machine.
It creates a python virtual environment called `venv` in the `venv/` folder in your working directory and activates it.
Since almost all our dependencies are Python packages, it will then install them from the `requirements.txt` file to this venv.

It then checks if you have Redis installed on your machine and if not installs it using homebrew.

### Controlling an exhibition

There are multiple MAKEFILE commands available to set up and close an exhibition.

- `make setup`: Sets up the Redis server on the designated port, runs the Flask app and records its process ID (`PID`) into a file.

  - You can now go into your browser and open the user-input interface at `localhost:5001` and the Froschteich at `localhost:5001/Froschteich`.
    N.B. that these are the standard ports and if you cannot find anything there, the `flask_app.py` script might have changes to the port of the Flask app.

  > N.B. You might need to open up a second terminal to execute further commands once the app
  > is running in case the app does not give you the terminal back.

- `make reset_redis`: resets the Redis cache to make all images have 0 clicks again in case the case was still populated from an earlier exhibition.
- `make enable_logging` / `make disable_logging` / `make logging_stauts`: Currently, logging is enabled on startup.
  If you want to test that the user-input frontend works without logging these test clicks,
  you can call the `make disable_logging` command.
  If you are unsure about the current status or want to double-check it, call the `make logging_stauts` command.
- `make stop`: Stop the app by killing its process stored in the `PID_FILE`, thereby deleting the file, if it exists.
- `make restart`: A convenience wrapper around `make stop` and `make setup`: Restart the app.

### Analysing the results

After you have collected the user input during an exhibition, your results are stored in CSV files on your file system. To compress them into a Parquet file and transform them into analysable data, you can run the `make analytics` command which will spin up dbt to transform your data and store them in a DuckDB file in the `./analytics/duckdb/` folder.

To query and visualise the data in the DuckDB, this app can spin up the software Metabase in a Docker container.
To start it, execute the `make start_metabase` command, which will build the image if it does not exist,
and spin up the container if it is not already running.

You can now access Metabase in your browser on `localhost:81` (standard port, defined by the `docker-compose.yml`).
The first time, you need to indicate an e-mail address and a password. Both are just used internally, and the e-mail can be fake for example. You might need to remember them later to log in again though.
We cannot cover how to use Metabase here, but we chose the software because it should be quite straightforward to use.

Once you are done, you can stop the Metabase container if you want, using `make stop_metabase`.

## The Frontend

## The Backend

### Flask

We are using the Flask framework to process the data created through the app. These are the main functionalities of the backend:

1. Controlling the app through API calls during a session to e.g. start the app, prevent event logging for testing purposes,
   stop the app, and start the post-processing of all session data.
2. Caching clicks per image in Redis to display on the fly in the Froschteich view.
3. Saving detailed information about each event in a permanent database for later analysis.

#### Endpoints

To serve the above purposes, the app has the following endpoints:

- `enable_logging` / `disable_logging` / `logging_stauts`:
  POSTing to these endpoints controls whether clicking on an image leads to an event being created for processing or not.
  In the beginning of an exhibition, it might be beneficial to test the frontend first and only enable logging after
  the session has started and guests are using the app.
- `log_selection`: This is the endpoint that gets called automatically when an image is clicked.
  If logging is enabled, it will perform two tasks.
  1. It will increment the click counter of the winning image in the Redis cache
  2. It will log the winning image, the losing image, and the timestamp of a click event to a CSV file.
- `get_counters` and `reset_counters`: These endpoints control the Redis cache.
  The first endpoint returns a JSON with the current click values for each image as a dictionary.
  The second endpoint resets the Redis cache to start with a clean slate on the Froschteich at the beginning of an exhibition.
  The cache is not automatically cleared when exiting the app to allow resuming a session in case of technical difficulties mid-exhibition.
- `get_images` and `serve_images`: Being mere utility functions, these endpoints only serve as a file serving mechanism with which the frontend can request images from the folders of the file system dynamically.
  The first endpoint lists all available images so the randomised frontend functions only choose from actually available images, and the second endpoint returns the actual image from the `IMAGE_FOLDER`,
- `froschteich`: Is called from within a browser to display the view of all frogs weighted by their current click counter.
- `index` : The main route of the app: Displays the user-input view where users can choose their favourite images.

### Analytics ETL

- Python script to:
  1. Process all CSV log files
     - Assign correct data types
     - mash all CSVs into one dataframe
  2. Write the dataframe to a Parquet file
     - If the Parquet file exceeds 100MB, a new one is created, otherwise it is appended
     - If no Parquet file (below 100MB) exists, a new one is created
  3. The used CSV files are pushed into the "processed" subfolder for possible backfills
- The Parquet file will be picked up by DuckDB later to process

## Analytics

The analytics is done through DBT writing into a local DuckDB for ease of use and to stay local
while still maintaining OLAP capabilities.

### Business Logic

The business logic here centres around three identifiable entities in the process:

- The **image**,
- The **user**,
- The **session** (i.e. the exhibition or event that the installation was exhibited.);
  although the "session" naming currently is somewhat ambiguous because in web analytics, idless of a particular user and the subsequent pickup after the idle time is often also referred to as a new "session" or "user session" starting.

We are later interested in the following questions:

- Which image has been the most successful in a given session or across all sessions?
- Against which image has a certain image lost/won most often?
- Can we see any particular patterns about which attributes of an image could predict its success on average?
- Which session was unusual in the types of image selected?

While the second question is quite easy to answer, the definition of when an
image is "successful" requires more exploration.

### Defining success: Personal vs. general

Naively speaking, an image is successful when it has won more "duels" than any
other image. What this logic obfuscates, however, is that some users simply
really like a particular image OR that no good contenders happened to be
selected in a particular user session.

To mitigate this, we are introducing a
**penalty factor** for subsequent wins. That means, the more often in a row an
image has won, the less information we obtain about its general success and the
more information about the particular user's preference. Thus, to account for the
diminishing general validity of a win streak of a particular image, we are
discounting each additional win by a multiplicative factor—until it reaches a
minimum influence after **X** subsequent wins.

### Metadata and properties

If we are to evaluate which properties predict success, we need to add these
properties as metadata later in the Analytics process.

### DBT und DuckDB

- dbt picks up all Parquet files in the "results" folder and reads them in
  through DuckDBs Parquet extension.
- In the first **staging layer**, all Parquet files are being combined and minor transformations are applied, such as casting
  timestamps to the Berlin timezone.
  - Most notably, we here also apply the user change, session change and streak logic. Whenever a certain amount of time has passed between logged events, a new `user_id` or `session_id` will be created (i.e. the previous one incremented.) Likewise,
    whenever two subsequent events have the same winning image, we increment a streak counter that serves as the basis for our later penalty mechanic.
- In the **transformation layer**, we add the metadata about images and sessions, as well as calculate the penalty factor.
- In the **presentation layer**, we create some pre-calculated data marts for viewing aggregates by session or by image.

### Metabase

As a lightweight data visualisation and query solution, Metabase is run from a container and accesses the DuckDB. It is used as a
BI tool.
To avoid confusion with often-used ports, we access Metabase through port 81.
