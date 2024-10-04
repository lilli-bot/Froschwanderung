import os
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import logging
from datetime import datetime

logger = logging.Logger(__name__)
logger.level = logging.INFO

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

input_folder = "results"
# The timestamp for our output Parquet file
# We assume that we will not exceed 1GB in size per month
# so we will use the current year and month
timestamp = datetime.now().strftime("%Y%m")

# Check if any parquet files exist, if not, we will initialise one using
# the current timestamp
parquet_files = [f for f in os.listdir(input_folder) if f.endswith(".parquet")]

output_file = f"{timestamp}.parquet"
file_found = False

# Determine the output file
for parquet_file in parquet_files:
    file_path = os.path.join(input_folder, parquet_file)
    if os.path.getsize(file_path) < (1 * 1024 * 1024 * 1024):
        output_file = parquet_file
        file_found = True
        break

# Log the result
if file_found:
    logger.info(f"Selected existing Parquet file: {output_file}")
else:
    logger.info(f"No suitable Parquet file found. Using new file: {output_file}")

# Let's determine the .CSV schema
csv_schema = {
    "event_id": "string",
    "clicked_image": "string",
    "not_clicked_image": "string",
}


def process_csv_to_parquet(input_folder, output_file=output_file):
    # Define paths
    processed_folder = os.path.join(input_folder, "processed")

    # Create the processed folder if it doesn't exist
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    # Collect all CSV files
    csv_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

    if not csv_files:
        logger.info("No CSV files to process.")
        return

    output_path = os.path.join(input_folder, output_file)
    # Initialize an empty DataFrame or read existing Parquet file if any exist
    if os.path.exists(output_path):
        combined_df = pd.read_parquet(output_path)
    else:
        combined_df = pd.DataFrame()

    for csv_file in csv_files:
        file_path = os.path.join(input_folder, csv_file)
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path, dtype=csv_schema, parse_dates=["timestamp"])
            logger.info(f"Processed {csv_file}.")
        except pd.errors.EmptyDataError:
            print(f"File {csv_file} is empty. Skipping.")
            continue
        except pd.errors.ParserError:
            print(f"File {csv_file} is malformed. Skipping.")
            continue

        # Ensure the timestamp column is properly converted to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Append the DataFrame to the combined DataFrame
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    # deduplicate eventual event_ids
    if combined_df["event_id"].duplicated().any():
        combined_df.drop_duplicates(subset=["event_id"], inplace=True)
        logger.warning("Duplicated 'event_id' values found. Removed duplicates.")

    if combined_df["event_id"].isnull().any():
        logger.warning("NULL values found in 'event_id' column.")
    if combined_df["timestamp"].isnull().any():
        logger.warning(
            f"NULL values found in 'timestamp' column for event_ids \
                        { combined_df[combined_df['event_id'].isnull()]['event_id'].to_list() }."
        )

    # Convert the combined DataFrame to a Parquet file
    table = pa.Table.from_pandas(combined_df)
    pq.write_table(table, os.path.join(input_folder, output_file))

    # Move the processed CSV files to the processed folder
    for csv_file in csv_files:
        file_path = os.path.join(input_folder, csv_file)
        processed_file_path = os.path.join(processed_folder, csv_file)
        os.rename(file_path, processed_file_path)

    logger.info(
        f"Processed {len(csv_files)} files. Combined data written to {output_file}."
    )


if __name__ == "__main__":
    process_csv_to_parquet(input_folder="results", output_file=output_file)
