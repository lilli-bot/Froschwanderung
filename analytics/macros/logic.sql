{%- macro extract_user_from_timestamp(timestamp_column) -%}
{# After X minutes of idle time between the rows, we assume that a 
  new user has entered #}
  CASE WHEN 
    date_sub('minute', 
              LAG({{ timestamp_column }}, 1) OVER (ORDER BY {{ timestamp_column }})::TIMESTAMP,
              {{ timestamp_column }}::TIMESTAMP) 
        > {{ var("new_user_after_minutes") }}
    THEN TRUE
    ELSE FALSE
    END
{%- endmacro -%}


{%- macro extract_session_from_timestamp(timestamp_column) -%}
{# If more than X hours have passed between new evens, we assume that a 
  new session has begun #}
  CASE WHEN 
    date_sub('hour', 
              LAG({{ timestamp_column }}, 1) OVER 
              (ORDER BY {{ timestamp_column }})::TIMESTAMP, 
              {{ timestamp_column }}::TIMESTAMP) 
        > {{ var('new_session_after_hours') }}
    THEN TRUE
    ELSE FALSE
    END

{%- endmacro -%}

