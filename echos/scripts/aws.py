import boto3
import botocore
import functools
from pathlib import Path
import yaml
import json
import sys
import uuid
from rich.console import Console

console = Console()

CONFIG_FILE = Path(__file__).parent.parent / 'aws_config.yaml'
CONFIG_TEMPLATE = {}


def load_template():
    with open(CONFIG_FILE, "r") as f:
        global CONFIG_TEMPLATE
        CONFIG_TEMPLATE = yaml.safe_load(f)

def dump_config():
    with open("echos.yaml", "w") as f:
        yaml.dump(CONFIG_TEMPLATE, f)

def load_config():
    with open("echos.yaml", "r") as f:
        global CONFIG_TEMPLATE
        CONFIG_TEMPLATE = yaml.safe_load(f)

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
def create_s3_bucket(session, bucket_region):
    client = session.client('s3')
    bucket_name = CONFIG_TEMPLATE['Resources']['EchosBucket']['Properties']['BucketName']
    client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
        'LocationConstraint': bucket_region})
    response = client.head_bucket(Bucket=bucket_name)
    if response['ResponseMetadata']['HTTPStatusCode'] == 409:
        raise Exception(f"S3 bucket {bucket_name} already exists")
    CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'][0]['Resource'] = [f"arn:aws:s3:::{bucket_name}" + '/*']



@update_status(msg="Deleting S3 bucket")
def delete_s3_bucket(session):
    client = session.client('s3')
    bucket_name = CONFIG_TEMPLATE['Resources']['EchosBucket']['Properties']['BucketName']
    response = client.head_bucket(Bucket=bucket_name)
    if response['ResponseMetadata']['HTTPStatusCode'] == 404:
        raise Exception(f"S3 bucket {bucket_name} does not exist")
    client.delete_bucket(Bucket=bucket_name)

@update_status(msg="Creating Lambda role")
def create_lambda_role(session, permissions_boundary_arn=None):
    client = session.resource('iam')
    role_name = CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['RoleName']
    assume_role_policy_json = json.dumps(CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['AssumeRolePolicyDocument'])
    policy_name = CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['Policies'][0]['PolicyName']
    policy_json = json.dumps(CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['Policies'][0]['PolicyDocument'])

    try:
        if permissions_boundary_arn is None:
            client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_json,)
        else:
            client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_json, PermissionsBoundary=permissions_boundary_arn)
            CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']["PermissionsBoundary"] = permissions_boundary_arn
        role_policy = client.RolePolicy(role_name, policy_name)
        role_policy.put(PolicyDocument=policy_json)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            console.print("IAM role already exists", style="bold blue")
        else:
            raise e

@update_status(msg="Deleting Lambda role")
def delete_lambda_role(session):
    role_name = CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['RoleName']
    policy_name = CONFIG_TEMPLATE['Resources']['EchosLambdaRole']['Properties']['Policies'][0]['PolicyName']

    client = session.resource('iam')    
    role_policy = client.RolePolicy(role_name, policy_name)
    role_policy.delete()
    client.Role(role_name).delete()