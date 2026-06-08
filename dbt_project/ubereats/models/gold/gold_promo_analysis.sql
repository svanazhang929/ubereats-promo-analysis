{{ config(materialized='table') }}

select
    promo_type,
    suburb,
    count(*) as restaurant_count,
    round(avg(rating), 3) as avg_rating,
    round(avg(review_count_num), 0) as avg_review_count,
    round(avg(delivery_fee), 2) as avg_delivery_fee,
    sum(has_promo) as promo_count,
    round(sum(has_promo) * 100.0 / count(*), 1) as promo_rate_pct
from {{ ref('silver_restaurants') }}
where rating is not null
group by 1, 2
order by 1, 2
