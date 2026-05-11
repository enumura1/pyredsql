query = """
select user_id, updated_at
from users
qualify row_number() over(partition by user_id order by updated_at desc)=1;
"""
