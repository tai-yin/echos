
from rich.console import Console
from rich.prompt import Prompt
from rich.pretty import pprint

import aws

console = Console()

def setup_infra():
    console.print(":trumpet:Setting up Echos", style="bold blue")

    use_existing_config = Prompt.ask("Do you want to use existing config? (y/n)", default="n")
    if use_existing_config == 'y':
        aws.load_config()
    else:
        aws.init_config()
        # AWS Profile
        aws_profile = Prompt.ask("Enter your AWS profile name")
        aws.CONFIG["AWSProfile"] = aws_profile
        # S3 Bucket
        bucket_region = Prompt.ask("Enter S3 bucket region", default="us-west-2")
        aws.CONFIG["S3BucketRegion"] = bucket_region
        # Lambda Role[optional permissions boundary]
        use_permissions_boundary = Prompt.ask("Do you want to use permissions boundary for lambda iam role? (y/n)", default="n")
        if use_permissions_boundary == 'y':
            permissions_boundary_arn = Prompt.ask("Enter your AWS permissions boundary arn")
            aws.CONFIG["LambdaRolePermissionBoundaryArn"] = permissions_boundary_arn
        
    console.print("Config: ", style="bold blue", end="")
    pprint(aws.CONFIG, expand_all=True)
    
    ok2go = Prompt.ask("Proceed to deploy? (y/n)", default="y")
    if ok2go == "y":
        aws.setup()
        console.print("Done!", style="bold blue")
    
if __name__ == '__main__':
    setup_infra()