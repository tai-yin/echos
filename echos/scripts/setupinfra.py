

import uuid
from rich.console import Console
from rich.prompt import Prompt
from rich.pretty import pprint

import aws

console = Console()

def setup_infra():
    console.print("Setting up Echos:trumpet:", style="bold blue")
    aws.load_config()

    # AWS Profile
    aws_profile = Prompt.ask("Enter your AWS profile name")
    session = aws.create_session(aws_profile)
    
    # AWS Account
    aws.get_caller_identity(session)
    
    # S3 Bucket
    create_s3_bucket = Prompt.ask("Do you want to create a S3 bucket for echos? (y/n)", default="y")
    if create_s3_bucket == 'y':
        bucket_region = Prompt.ask('Enter S3 bucket region', default="us-west-2")
        bucket_name = Prompt.ask('Enter S3 bucket name', default=f'echos-executions-{str(uuid.uuid4()).split("-")[0]}')
        aws.create_s3_bucket(session, bucket_region, bucket_name)
    else:
        bucket_name = Prompt.ask('Enter your existing S3 bucket name')
        aws.get_existing_s3_bucket(session, bucket_name)
        
    # Lambda Role[optional permissions boundary]
    create_lambda_role = Prompt.ask("Do you want to create an IAM role for AWS Lambda? (y/n)", default="y")
    if create_lambda_role == 'y':
        role_name = Prompt.ask("Enter your AWS Lambda role name", default="echos-lambda-role")
        use_permissions_boundary = Prompt.ask("Do you want to use permissions boundary? (y/n)", default="n")
        if use_permissions_boundary == 'y':
            permissions_boundary_arn = Prompt.ask("Enter your AWS permissions boundary arn")
            aws.create_lambda_role(session, role_name, permissions_boundary_arn)
    else:
        role_name = Prompt.ask("Enter your existing AWS Lambda role name")
    aws.create_lambda_role(session, role_name)
    
    console.print("Config: ", style="bold blue", end="")
    pprint(aws.CONFIG_TEMPLATE, expand_all=True)
    
    aws.dump_config()
    
if __name__ == '__main__':
    setup_infra()