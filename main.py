import boto3;

SETUP_COMPLETED = False


def create_client(service_name, aws_access_key_id, aws_secret_access_key, dry_run=False):
    return boto3.client(
        service_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        dry_run=dry_run
    )




print("Welcome to EZ Cracker!")

if (not SETUP_COMPLETED): # Placeholder for now, need to add detection for presence of credentials in .env file
    print("Looks like you haven't set up your AWS credentials yet. Let's do that now.")
    aws_access_key_id = input("Enter your AWS Access Key ID: ")
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
    print("Please wait while I validate your credentials...")
    
    client = create_client("ec2", aws_access_key_id, aws_secret_access_key, True)
    try:
        client.list_users()
        print("Success! Your credentials are valid.")
        SETUP_COMPLETED = True
    except:
        print("Error: Your credentials are invalid. Please try again.")
        exit()

