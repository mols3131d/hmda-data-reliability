select
    cast(yellow_trips.pickup_date as varchar)
    || ':'
    || cast(yellow_trips.pickup_location_id as varchar) as mart_grain_key,
    yellow_trips.pickup_date,
    yellow_trips.pickup_location_id,
    zones.borough as pickup_borough,
    zones.zone as pickup_zone,
    zones.service_zone as pickup_service_zone,
    count(*) as trip_count,
    sum(yellow_trips.total_amount) as total_amount,
    avg(yellow_trips.total_amount) as average_total_amount,
    sum(coalesce(yellow_trips.passenger_count, 0)) as total_passenger_count
from {{ ref('stg_yellow_tripdata') }} as yellow_trips
left join {{ ref('stg_taxi_zones') }} as zones
    on yellow_trips.pickup_location_id = zones.location_id
where yellow_trips.pickup_date is not null
    and yellow_trips.pickup_location_id is not null
group by
    yellow_trips.pickup_date,
    yellow_trips.pickup_location_id,
    zones.borough,
    zones.zone,
    zones.service_zone
