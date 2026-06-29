select
    cast(activity_year as varchar)
    || ':'
    || coalesce(state_code, 'unknown')
    || ':'
    || cast(loan_purpose as varchar) as mart_grain_key,
    activity_year,
    state_code,
    loan_purpose,
    count(*) as application_count,
    sum(case when action_taken in (1, 2) then 1 else 0 end) as approval_count,
    sum(case when action_taken in (3, 7) then 1 else 0 end) as denial_count,
    round(
        1.0 * sum(case when action_taken in (1, 2) then 1 else 0 end)
        / nullif(count(*), 0),
        6
    ) as approval_rate,
    avg(loan_amount) as average_loan_amount,
    avg(income) as average_income
from {{ ref('stg_hmda_loans') }}
where activity_year is not null
    and state_code is not null
    and loan_purpose is not null
group by
    activity_year,
    state_code,
    loan_purpose
