query = """
UNLOAD ('SELECT * FROM users')
TO '<s3-path>'
IAM_ROLE '<iam-role-arn>'
FORMAT AS PARQUET;
"""
