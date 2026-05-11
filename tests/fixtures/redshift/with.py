query = """
with base as (
  select user_id, updated_at
  from users
)
select *
from base;
"""
