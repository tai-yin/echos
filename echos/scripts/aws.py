import boto3
from botocore.exceptions import ClientError
from samcli.cli.main import cli
from samcli.cli.context import Context
import functools
from pathlib import Path
import yaml
import sys
import uuid
import os
from subprocess import Popen
from rich.console import Console

console = Console()

CONFIG_FILE = Path(__file__).parent / 'aws_config.yaml'
TEMPLATE_FILE = Path(__file__).parent / 'samcli_template.yaml'

CONFIG = {}
TEMPLATE = {}

def update_status(msg):
    '''decorator for console status update'''
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

@update_status(msg="Initiating...")
def init_config():
    with open(CONFIG_FILE, "r") as f:
        global CONFIG
        CONFIG = yaml.safe_load(f)
    echos_short_id = uuid.uuid4().hex[:8]
    CONFIG['AWSProfile'] = os.environ.get('AWS_PROFILE', 'Unknown')
    CONFIG['S3BucketRegion'] = "us-west-2"
    CONFIG['S3BucketName'] = f"echos-execution-bucket-{echos_short_id}"
    CONFIG["LambdaName"] = f"echos-execution-lambda-{echos_short_id}"

@update_status(msg="...")
def dump_config():
    with open("echos-config.yaml", "w") as f:
        yaml.dump(CONFIG, f)

@update_status(msg="...")
def load_config():
    try:
        with open("echos-config.yaml", "r") as f:
            global CONFIG
            CONFIG = yaml.safe_load(f)
    except FileNotFoundError:
        raise Exception("Config file 'echos-config.yaml' not found. Please run setup first.")

@update_status(msg="...")
def dump_samcli_template():
    with open("echos-template.yaml", "w") as f:
        yaml.dump(TEMPLATE, f)

@update_status(msg="...")
def load_samcli_template():
    with open(TEMPLATE_FILE, "r") as f:
        global TEMPLATE
        TEMPLATE = yaml.safe_load(f)

@update_status(msg="Creating AWS session")
def create_session(profile_name):
    session = boto3.Session(profile_name=profile_name)
    client = session.client('sts')
    client.get_caller_identity()
    os.environ["AWS_PROFILE"] = profile_name
    return session

@update_status(msg="Creating S3 bucket")
def create_s3_bucket(session, bucket_name, bucket_region):
    client = session.client('s3')
    try:
        response = client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
            'LocationConstraint': bucket_region})
    except ClientError as e:
        raise e

@update_status(msg="Deleting S3 bucket")
def delete_s3_bucket(session, bucket_name):
    client = session.client('s3')
    response = client.head_bucket(Bucket=bucket_name)
    if response['ResponseMetadata']['HTTPStatusCode'] == 404:
        raise Exception(f"S3 bucket {bucket_name} does not exist")
    client.delete_bucket(Bucket=bucket_name)

def setup():
    
    load_samcli_template()
    TEMPLATE["Resources"]["EchosExecutor"]["Properties"]["FunctionName"] = CONFIG["LambdaName"]
    TEMPLATE["Resources"]["EchosExecutor"]["Properties"]["Policies"][0]["Statement"][0]["Resource"] = f'arn:aws:s3:::{CONFIG["S3BucketName"]}/*'
    
    permission_boundary_arn = CONFIG.get("LambdaRolePermissionBoundaryArn", None)
    if permission_boundary_arn is not None:
        TEMPLATE["Globals"] = {
            "Function": {
                "PermissionsBoundary":permission_boundary_arn
            }
        }
    
    session = create_session(CONFIG["AWSProfile"])
    # create_s3_bucket(session, CONFIG["S3BucketName"], CONFIG["S3BucketRegion"])
    
    dump_config()
    dump_samcli_template()
    
    build_process = Popen(["sam", "build", "--template-file", "echos-template.yaml", "--base-dir", "echos-src","--build-dir", "echos-build"], stdout=sys.stdout, stderr=sys.stderr)
    build_process.wait()
    
    package_process = Popen(["sam", "package", "--template-file", "echos-build/template.yaml", "--s3-bucket", CONFIG["S3BucketName"], "--s3-prefix", "lambda", "--output-template-file", "echos-packaged.yaml"], stdout=sys.stdout, stderr=sys.stderr)
    package_process.wait()

    sys.exit(0)