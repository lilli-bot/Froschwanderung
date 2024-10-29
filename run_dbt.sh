export DBT_PROFILES_DIR=$(pwd)/analytics
echo "dbt profiles directory: $DBT_PROFILES_DIR"
export DBT_PROJECT_DIR=$(pwd)/analytics
echo "dbt project directory: $DBT_PROJECT_DIR"

dbt run --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROJECT_DIR