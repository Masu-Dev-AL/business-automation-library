import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Triggered when PDF uploaded to incoming bucket
    Invokes Bedrock Data Automation to process the invoice
    Stores original filename as S3 metadata for later retrieval
    """
    
    try:
        # Create client inside function with latest boto3
        bedrock_runtime = boto3.client('bedrock-data-automation-runtime', region_name='us-east-1')
        
        # Get S3 event details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"New PDF uploaded: s3://{bucket}/{key}")
        
        # Invoke Bedrock Data Automation
        response = bedrock_runtime.invoke_data_automation_async(
            dataAutomationConfiguration={
                'dataAutomationProjectArn': os.environ['BEDROCK_PROJECT_ARN']
            },
            inputConfiguration={
                's3Uri': f's3://{bucket}/{key}'
            },
            outputConfiguration={
                's3Uri': os.environ['OUTPUT_BUCKET']
            },
            dataAutomationProfileArn=os.environ['BEDROCK_PROFILE_ARN']
        )
        
        invocation_arn = response['invocationArn']
        job_id = invocation_arn.split('/')[-1]
        
        print(f"✓ Bedrock invocation started: {invocation_arn}")
        print(f"Job ID: {job_id}")
        
        # Tag the original PDF with job_id for later retrieval
        s3.put_object_tagging(
            Bucket=bucket,
            Key=key,
            Tagging={
                'TagSet': [
                    {'Key': 'bedrock_job_id', 'Value': job_id},
                    {'Key': 'processing_status', 'Value': 'in_progress'}
                ]
            }
        )
        
        print(f"✓ Tagged PDF with job_id: {job_id}")
        
        return {
            'statusCode': 200,
            'invocationArn': invocation_arn,
            'job_id': job_id,
            'original_key': key,
            'message': f'Processing started for {key}'
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'error': str(e)
        }