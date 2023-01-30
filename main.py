import boto3;

SETUP_COMPLETED = False

# Create a boto3 client to interact with AWS services that accepts the AWS credentials as parameters
def create_client(service_name, aws_access_key_id, aws_secret_access_key):
    return boto3.client(
        service_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )




print("Welcome to EZ Cracker!")

if (not SETUP_COMPLETED): # Placeholder for now, need to add detection for presence of credentials in .env file
    print("Looks like you haven't set up your AWS credentials yet. Let's do that now.")
    aws_access_key_id = input("Enter your AWS Access Key ID: ")
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
    print("Please wait while I validate your credentials...")
    
    client = create_client("iam", aws_access_key_id, aws_secret_access_key)

