import boto3;
import os
import dotenv
from botocore.exceptions import ClientError

TEST_AMI_ID = "ami-05bfbece1ed5beb54" # Ubuntu 18.04 AMI

def dotenv_present():
    try:
        with open(".env", "r") as f:
            dotenv = f.read()
        return True
    except:
        return False

def set_credentials(aws_access_key_id, aws_secret_access_key):
    with open(".env", "w") as f:
        f.write("AWS_ACCESS_KEY_ID=" + aws_access_key_id)
        f.write("\nAWS_SECRET_ACCESS_KEY=" + aws_secret_access_key)

print("Welcome to EZ Cracker!")

if (not dotenv_present()):
    print("Looks like you haven't set up your AWS credentials yet. Let's do that now.")
    aws_access_key_id = input("Enter your AWS Access Key ID: ")
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
    print("Please wait while I validate your credentials...")

    try:
        client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
        client.run_instances(ImageId=TEST_AMI_ID, MinCount=1, MaxCount=1, InstanceType='t2.micro', DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print("Error: Your credentials are invalid. Please make sure you entered them correctly.")
            raise e
        else:
            print("Success! Your credentials are valid.")
            set_credentials(aws_access_key_id, aws_secret_access_key)
    except:
        print("Sorry, there was an error validating your credentials. Please try again.")
        exit()


try:
    dotenv.load_dotenv()
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
except:
    print("Error: Your credentials are invalid. Please make sure the credentials in your .env file are correct.")
    exit()


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






