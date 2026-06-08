{{ config(materialized='table') }}

select
    name,
    suburb,
    rating,
    review_count,
    delivery_fee,
    delivery_time_min,
    delivery_time_max,
    price_tier,
    promo_label,
    promo_type,
    is_sponsored,
    scraped_at,
    current_timestamp as ingested_at
from read_ndjson_auto('/Users/svana/ubereats-promo-analysis/data/raw/restaurants_20260609_0127.jsonl')
