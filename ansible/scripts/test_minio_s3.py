import boto3
from botocore.client import Config
import os

# Config
minio_endpoint = "http://10.134.12.9:9000"  # any worker IP
access_key = "minioadmin"
secret_key = "minioadmin"
bucket_name = "qasm-data"
test_file = "example.qasm"

# Client setup
s3 = boto3.client(
    "s3",
    endpoint_url=minio_endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# Create bucket (ignore if already exists)
try:
    s3.create_bucket(Bucket=bucket_name)
except s3.exceptions.BucketAlreadyOwnedByYou:
    pass

# Upload a test file
with open(test_file, "w") as f:
    f.write("OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0],q[1];")

s3.upload_file(test_file, bucket_name, test_file)
print(f"Uploaded {test_file} to bucket {bucket_name}")

# Download and read back to verify
s3.download_file(bucket_name, test_file, f"downloaded_{test_file}")
with open(f"downloaded_{test_file}") as f:
    print("Downloaded content:")
    print(f.read())
