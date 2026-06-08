select
    cast(tpep_pickup_datetime as timestamp) as pickup_at,
    cast(tpep_dropoff_datetime as timestamp) as dropoff_at,
    cast(tpep_pickup_datetime as date) as pickup_date,
    cast(PULocationID as integer) as pickup_location_id,
    cast(DOLocationID as integer) as dropoff_location_id,
    cast(passenger_count as bigint) as passenger_count,
    cast(total_amount as double) as total_amount,
    cast(source_partition as varchar) as source_partition,
    cast(source_file as varchar) as source_file
from {{ source('raw', 'yellow_tripdata') }}
