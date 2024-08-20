# Froschwanderung

Interactive [Frog] Ranking Game

## Idea and Purpose

## How to Use?

## The Frontend

## The Backend

## Flask

## Analytics ETL

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

To mitiage this, we are introducing a
**penality factor** for subsequent wins. That means, the more often in a row an
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
