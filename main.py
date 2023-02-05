import boto3;
import os
import dotenv

SETUP_COMPLETED = False
TEST_AMI_ID = "ami-05bfbece1ed5beb54"






print("Welcome to EZ Cracker!")

if (not SETUP_COMPLETED): # Placeholder for now, need to add detection for presence of credentials in .env file
    print("Looks like you haven't set up your AWS credentials yet. Let's do that now.")
    aws_access_key_id = input("Enter your AWS Access Key ID: ")
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
    print("Please wait while I validate your credentials...")

    try:
        client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
        client.run_instances(ImageId=TEST_AMI_ID, MinCount=1, MaxCount=1, InstanceType='t2.micro', DryRun=True)
    except DryRunOperation:
        SETUP_COMPLETED = True
        print("Success! Your credentials are valid.")
    except:
        print("Error: Your credentials are invalid. Please make sure you entered them correctly.")
        exit()

else:
    try:
        dotenv.load_dotenv()
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    except:
        print("Error: Your credentials are invalid. Please make sure the credentials in your .env file are correct.")
        exit()

    print("Looks like you've already set up your AWS credentials. Let's get started!")
    _hash = input("Enter the hash you want to crack: ")
    print("Please wait while I crack your hash...")
    sqs = boto3.resource('sqs')
    queue = sqs.create_queue(QueueName='hash_queue', Attributes={'DelaySeconds': '5'})
    print(queue.url)
    queue.delete()
    
    # try:
    # except:    
    #     print("Error: There was an error creating the SQS queue. Please try again.")
    #     raise SystemExit

    # Create an SQS queue to send this hash to an EC2 instance
    # Create an EC2 instance to crack the hash
    # Wait for the EC2 instance to crack the hash
    # Print the cracked hash





