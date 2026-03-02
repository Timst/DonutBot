with rate_14d as (
    select username
         , count(distinct id) as entry_count
         , sum(number) as total_number
         , 14.0 as days_sampled
         , sum(number)/14.0 as donuts_per_day
         , count(distinct id)/14.0 as entries_per_day
    from cleaned_records
    where time BETWEEN date('now', '-14 days') AND date('now')
      and number != 0
    group by username 
)

, rate_28d as (
    select username
         , count(distinct id) as entry_count
         , sum(number) as total_number
         , 28.0 as days_sampled
         , sum(number)/28.0 as donuts_per_day
         , count(distinct id)/28.0 as entries_per_day
    from cleaned_records
    where time BETWEEN date('now', '-14 days') AND date('now')
      and number != 0
    group by username 
)

, all_time as (
    select username
         , count(distinct id) as entry_count
         , sum(number) as total_number
         , julianday('now') - julianday('2026-01-15') as days_sampled
         , sum(number)/(julianday('now') - julianday('2026-01-15')) as donuts_per_day
         , count(distinct id)/(julianday('now') - julianday('2026-01-15')) as entries_per_day
    from cleaned_records
    where number != 0
    group by username 
)

, modeled_rates as (
    select username
         , all_time.total_number as current_total
         , case when rate_14d.entry_count > 1 and rate_14d.total_number > 4 then rate_14d.days_sampled
                when rate_28d.entry_count > 1 and rate_28d.total_number > 4 then rate_28d.days_sampled
                else all_time.days_sampled
                end
             as days_sampled
         , case when rate_14d.entry_count > 1 and rate_14d.total_number > 4 then rate_14d.entry_count
                when rate_28d.entry_count > 1 and rate_28d.total_number > 4 then rate_28d.entry_count
                else all_time.entry_count
                end
             as entries_sampled
         , case when rate_14d.entry_count > 1 and rate_14d.total_number > 4 then rate_14d.total_number
                when rate_28d.entry_count > 1 and rate_28d.total_number > 4 then rate_28d.total_number
                else all_time.total_number
                end
             as donuts_sampled
         , case when rate_14d.entry_count > 1 and rate_14d.total_number > 4 then rate_14d.entries_per_day
                when rate_28d.entry_count > 1 and rate_28d.total_number > 4 then rate_28d.entries_per_day
                else all_time.entries_per_day
                end
             as entries_per_day
         , case when rate_14d.entry_count > 1 and rate_14d.total_number > 4 then rate_14d.donuts_per_day
                when rate_28d.entry_count > 1 and rate_28d.total_number > 4 then rate_28d.donuts_per_day
                else all_time.donuts_per_day
                end
             as donuts_per_day 
    from all_time
    left join rate_28d using (username)
    left join rate_14d using (username)
)

, final_rates as (
    select username
         , current_total
         , cast(round(days_sampled) as int) as days_sampled
         , donuts_sampled
         , entries_sampled
         , round(donuts_per_day, 2) as donuts_per_day
         , round(entries_per_day, 2) as entries_per_day
         , datetime('now') as refresh_time
    from modeled_rates
)

select * from final_rates