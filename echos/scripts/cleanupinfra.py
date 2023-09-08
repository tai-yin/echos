from rich.console import Console
from rich.prompt import Prompt
from rich.pretty import pprint
import aws
console = Console()
def cleanup_infra():
    aws.load_config()
    
    # AWS Profile
    aws_profile = Prompt.ask("Enter your AWS profile name")
    session = aws.create_session(aws_profile)
    
    aws.get_caller_identity(session)
    
    confirm_cleanup = Prompt.ask("Are you sure to clean up echos? (y/n)", default="y")
    if confirm_cleanup == 'y':
        aws.delete_s3_bucket(session)
        aws.delete_lambda_role(session)
    
    console.print("cleanup is done!", style="bold blue")
if __name__ == '__main__':
    cleanup_infra()