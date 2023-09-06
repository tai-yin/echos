import json
import logging
import boto3

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    logger.setLevel(logging.DEBUG)
    return "success"
    
    