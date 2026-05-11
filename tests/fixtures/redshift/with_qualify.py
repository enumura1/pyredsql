query = """
with base as (
  select user_id, updated_at
  from users
)
select *
from base
qualify row_number() over(partition by user_id order by updated_at desc)=1;
"""
