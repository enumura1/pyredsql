query = """
COPY users
FROM '<s3-path>'
IAM_ROLE '<iam-role-arn>'
FORMAT AS CSV
IGNOREHEADER 1;
"""
