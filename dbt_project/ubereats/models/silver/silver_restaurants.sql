{{ config(materialized='table') }}

select
    name,
    suburb,
    rating,
    case
        when review_count like '%k%' then cast(replace(review_count, 'k', '') as float) * 1000
        when review_count like '%+%' then cast(replace(review_count, '+', '') as float)
        else try_cast(review_count as float)
    end as review_count_num,
    delivery_fee,
    delivery_time_min,
    delivery_time_max,
    price_tier,
    promo_label,
    coalesce(promo_type, 'No Promotion') as promo_type,
    case when promo_type is not null then 1 else 0 end as has_promo,
    is_sponsored,
    scraped_at
from {{ ref('bronze_restaurants') }}
where name is not null
  and length(name) < 80
