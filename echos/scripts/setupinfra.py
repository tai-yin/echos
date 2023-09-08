
from rich.console import Console
from rich.prompt import Prompt
from rich.pretty import pprint

import aws

console = Console()

def setup_infra():
    console.print(":trumpet:Setting up Echos", style="bold blue")
    aws.load_template()

    # AWS Profile
    aws_profile = Prompt.ask("Enter your AWS profile name")
    session = aws.create_session(aws_profile)
    
    # AWS Account
    aws.get_caller_identity(session)
    
    # S3 Bucket
    bucket_region = Prompt.ask('Enter S3 bucket region', default="us-west-2")
    aws.create_s3_bucket(session, bucket_region)
        
    # Lambda Role[optional permissions boundary]
    use_permissions_boundary = Prompt.ask("Do you want to use permissions boundary for lambda iam role? (y/n)", default="n")
    if use_permissions_boundary == 'y':
        permissions_boundary_arn = Prompt.ask("Enter your AWS permissions boundary arn")
        aws.create_lambda_role(session, permissions_boundary_arn)
    else:
        aws.create_lambda_role(session)
    
    console.print("Config: ", style="bold blue", end="")
    pprint(aws.CONFIG_TEMPLATE, expand_all=True)
    
    aws.dump_config()
    
if __name__ == '__main__':
    setup_infra()