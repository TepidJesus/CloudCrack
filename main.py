import boto3;
import os
import dotenv
from botocore.exceptions import ClientError

import sys, getopt

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

def run_setup():
    print("Welcome to the EZ Cracker setup wizard!")
    print("Lets get started by setting up your AWS credentials. You can find these instructions for this in the setup guide in the README.md file.")

    while True:
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
                break
        except:
            print("Sorry, there was an error validating your credentials. Check you have enabled the correct permissions.")

argv = sys.argv[1:]
opts, args = getopt.getopt(argv, "hi:I:t:w:o:s", ["help", "inputHash", "hashFile", "hashType", "wordlist", "outputFile", "setup"])

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print("Example: main.py -i <inputHash> -I <inputFile> -t <hashType>, -w <wordlist>\n")
        print("Options:")
        print("     -h, --help                        Show This Menue")
        print("     -i, --inputHash      <inputHash>  The hash to be cracked")
        print("     -I, --hashFile       <inputFile>  The loaction of a txt file with a list of hashes to crack  (e.g /home/user/Desktop/hashes.txt)")
        print("     -t, --hashType       <hashType>   The type of hash to be cracked (e.g md5, sha1, sha256, sha512)")
        print("     -w, --wordlist       <wordlist>   The name of a wordlist from the Seclists repository (e.g rockyou.txt). The repository can be found at https://github.com/danielmiessler/SecLists/tree/master/Passwords")
        print("     -o, --outputFile     <outputFile> The location of the output file (e.g /home/user/Desktop/output.txt). Will output to the console if not specified.")
        print("     -s, --setup                      Run the setup wizard")
        sys.exit()
    elif opt in ("-s", "--setup"):
        run_setup()
    elif opt in ("-i", "--inputHash"):
        print("Input Hash is: " + arg)
        user_hash = arg
    elif opt in ("-I", "--hashFile"):
        hash_file = arg
        try:
            with open(hash_file, "r") as f:
                hashes = f.read()
        except:
            print("Error: The file you specified does not exist. Please make sure you have entered the correct path.")
            exit()
    elif opt in ("-t", "--hashType"):
        hash_type = arg
    elif opt in ("-w", "--wordlist"):
        wordlist = arg
    elif opt in ("-o", "--outputFile"):
        output_file = arg
        print("Output File is: " + arg + "")
        sys.exit()
    else:
        print("Invalid Option. Please use -h or --help for more information.")


print("Welcome to EZ Cracker!")

if (not dotenv_present()):
    print("Error: You have not set up your AWS credentials. Please run the setup wizard by using the -s or --setup flag.")
    exit()

try:
    dotenv.load_dotenv()
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
except:
    print("Error: Your credentials are invalid. Run --setup again if your credentials have changed.")
    exit()

if hash_file == None or hash_file == "":
    
_hash = input("Enter the hash you want to crack: ")
print("Please wait while I crack your hash...")

sqs = boto3.resource('sqs')
queue = sqs.create_queue(QueueName='hash_queue', Attributes={'DelaySeconds': '5'})
print(queue.url)
queue.delete()







