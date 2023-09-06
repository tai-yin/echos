import boto3
import botocore
import functools
from pathlib import Path
import yaml
import json
import sys
from rich.console import Console

console = Console()

CONFIG_FILE = Path(__file__).parent.parent / 'aws_lambda_config.yaml'
CONFIG_TEMPLATE = {}


def load_config():
    with open(CONFIG_FILE, "r") as f:
        global CONFIG_TEMPLATE
        CONFIG_TEMPLATE = yaml.safe_load(f)

def dump_config():
    with open("echos.yaml", "w") as f:
        yaml.dump(CONFIG_TEMPLATE, f)

def update_status(msg):
    '''decorator for timing and status update'''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # create string for status update
            try:
                with console.status(f"[bold green] {msg} ", spinner="bouncingBar") as status:
                    result = func(*args, **kwargs)
                    return result
            except Exception as e:
                console.print("Error: ", style="bold red", end="")
                console.print(e, highlight=False)
                sys.exit(1)
        return wrapper
    return decorator

@update_status(msg="Creating AWS session")
def create_session(profile_name):
    return boto3.Session(profile_name=profile_name)

@update_status(msg="Getting AWS caller identity")
def get_caller_identity(session):
    client = session.client('sts')
    identity = client.get_caller_identity()
    console.print(f"AWS Account: {identity['Account']}", style="bold blue")

@update_status(msg="Creating S3 bucket")
def create_s3_bucket(session, bucket_region, bucket_name):
    client = session.client('s3')
    client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
        'LocationConstraint': bucket_region})
    response = client.head_bucket(Bucket=bucket_name)
    if response['ResponseMetadata']['HTTPStatusCode'] == 409:
        raise Exception(f"S3 bucket {bucket_name} already exists")
    CONFIG_TEMPLATE['Resources']['EchosExecutor']['Properties']['Policies'][0]['Statement'][0]['Resource'] = [f"arn:aws:s3:::{bucket_name}" + '/*']

@update_status(msg="Getting S3 bucket")
def get_existing_s3_bucket(session, bucket_name):
    client = session.client('s3')
    response = client.head_bucket(Bucket=bucket_name)
    if response['ResponseMetadata']['HTTPStatusCode'] == 404:
        raise Exception(f"S3 bucket {bucket_name} does not exist")
    CONFIG_TEMPLATE['Resources']['EchosExecutor']['Properties']['Policies'][0]['Statement'][0]['Resource'] = [f"arn:aws:s3:::{bucket_name}" + '/*']

@update_status(msg="Creating Lambda role")
def create_lambda_role(session, role_name, permissions_boundary_arn=None):
    assume_role_policy_json = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            },
            {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            },
        ]
    })
    
    role_policy_json = json.dumps(CONFIG_TEMPLATE['Resources']['EchosExecutor']['Properties']['Policies'])
    
    client = session.resource('iam')
    if permissions_boundary_arn is None:
        client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_json,)
    else:
        client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_json, PermissionsBoundary=permissions_boundary_arn)

    role_policy = client.RolePolicy(role_name, '{}-permissions'.format(role_name))
    role_policy.put(PolicyDocument=role_policy_json)
    CONFIG_TEMPLATE["Globals"]["Function"]["PermissionsBoundary"] = permissions_boundary_arn