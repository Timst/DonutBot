with deletes as (
    select * from records where operation = "delete"
)

, adds as (
    select * from records where operation = "add"
)

, corrections_calculation as (
select adds.username as username
     , adds.id as id
     , adds.number as number
     , adds.time as time
     , case when deletes.number - sum(adds.number) over (partition by deletes.id order by adds.time desc) >= 0
            then -1*adds.number
            else -1*max(adds.number + deletes.number - sum(adds.number) over (partition by deletes.id order by adds.time desc), 0)
            end
         as correction
     , deletes.id as delete_id
     , deletes.number as delete_number
     , deletes.time as delete_time
from deletes
left join adds
  on (
    adds.username = deletes.username
    and adds.time < deletes.time
  )
)

, corrections as (
    select username, id, group_concat(delete_id, '|') as delete_id, max(-1*number, sum(correction)) as correction
    from corrections_calculation
    where correction != 0
    group by username, id, number
)

, corrections_overflow as (
    select '_' + cast(id as string) as id
         , username
         , number + sum(correction) as number
         , time
         , 'add' as operation
         , 0 as original_number
         , -1*(number + sum(correction)) as deleted_number
         , group_concat(delete_id, '|') as delete_record_id
    from corrections_calculation
    where correction != 0
    group by username, id, number
    having number + sum(correction) < 0
)

, cleaned_records as (
    select cast(adds.id as string) as id
         , adds.username
         , adds.number + coalesce(corrections.correction, 0) as number
         , adds.time
         , adds.operation
         , adds.number as original_number
         , -1 * coalesce(corrections.correction, 0) as deleted_number
         , cast(coalesce(delete_id, 0) as string) as delete_record_id
    from adds
    left join corrections
      on adds.id = corrections.id

    union all

    select * from corrections_overflow
)

select *
     , datetime('now') as refresh_time 
from cleaned_records