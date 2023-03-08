import boto3;
import os
import dotenv
import json
from botocore.exceptions import ClientError
import sys, getopt
import time
from job_handler import JobHandler, Job, STATUS, Command
import signal

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
                print("You're all set! Have fun, but remember to be safe and to only use this tool for legitimate purposes.")
                break
        except:
            print("Sorry, there was an error validating your credentials. Check you have enabled the correct permissions.")

def get_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except:
        print("Error: The config file does not exist. Did you delete it? Go get a new one from the repository, it's kind of important.")
        exit()
    return config

def check_file_presence(file_location):
    try:
        with open(file_location, "r") as f:
            file = f.read()
        return True
    except:
        return False
    
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    cleanup()
    print("All resources have been deleted. Goodbye!")
    sys.exit(0)

def cleanup():
    sqs = boto3.resource('sqs')
    queues = sqs.queues.all()
    for queue in queues:
        queue.delete()

    ec2 = boto3.resource('ec2')
    instances = ec2.instances.all()
    for instance in instances:
        instance.terminate()

def valid_mask(mask):
    if mask == None:
        return False
    
    if "?" not in mask:
        return False
    
    if len(mask) <= 1:
        return False
    
    for i in range(len(mask)):
        char = mask[i]
        if char != "?" and char != "d" and char != "l" and char != "u" and char != "s" and char != "a" and char != "h" and char != "H" and char != "b":
            return False
        if char == "?" and i % 2 != 0:
            return False
        if char != "?" and i % 2 == 0:
            return False
    return True


# TODO: Add wizard to walk new user through cracking a hash
argv = sys.argv[1:]
opts, args = getopt.getopt(argv, "ha:i:I:t:m:w:o:s:", ["help", "attackType", "inputHash", "hashFile", "hashType", "wordlist", "outputFile", "setup"])
hash_file = None
user_hash = None
attack_type = None
for opt, arg in opts:
    if opt in ("-h", "--help"):
        print("Example: main.py -i <inputHash> -I <inputFile> -t <hashType>, -w <wordlist>\n")
        print("Options:")
        print("     -h, --help                        Show This Menue")
        print("     -i, --inputHash      <inputHash>  The hash to be cracked")
        print("     -a, --attackType     <attackType> The type of attack to be used (e.g dictionary (0), mask (3))")
        print("     -I, --hashFile       <inputFile>  The loaction of a txt file with a list of hashes to crack  (e.g /home/user/Desktop/hashes.txt)")
        print("     -t, --hashType       <hashType>   The type of hash to be cracked (e.g md5, sha1, sha256, sha512)")
        print("     -m, --mask           <mask>       The mask to be used for the mask attack (e.g ?d?d?d?d). See https://hashcat.net/wiki/doku.php?id=mask_attack for more information.")
        print("     -w, --wordlist       <wordlist>   The name and location of a wordlist (e.g /home/user/rockyou.txt).")
        print("     -o, --outputFile     <outputFile> The location of the output file (e.g /home/user/Desktop/output.txt). Will output to the console if not specified.")
        print("     -s, --setup                       Run the setup wizard")
        sys.exit()
    
    elif opt in ("-s", "--setup"):
        run_setup()
        sys.exit()
    elif opt in ("-a", "--attackType"):
        attack_type = arg
        if attack_type == None:
            print("Error: You must specify an attack type.")
            attack_type = input("Please enter an attack type (e.g dictionary (0), mask (3)): ")
    elif opt in ("-i", "--inputHash"):
        user_hash = arg
        if user_hash == None:
            print("Error: You must specify a hash.")
            user_hash = input("Please enter a hash: ")
    elif opt in ("-I", "--hashFile"):
        hash_file = arg
        if not check_file_presence(hash_file):
            print("Error: The file you specified does not exist. Please check the file path and try again.")
            exit()
        if user_hash != None:
            print("Error: You cannot specify both a hash and a hash file! Please try again.")
            exit()
    elif opt in ("-t", "--hashType"):
        hash_type = arg
        if hash_type == None:
            print("Error: You must specify a hash type.")
            hash_type = input("Please enter a hash type (hint: Use the hash codes found on the hashcat wiki): ")
    elif opt in ("-m", "--mask"):
        mask = arg
        while not valid_mask(mask):
            print("Error: The mask you specified is invalid. Please check the mask and try again.")
            mask = input("Please enter a mask (e.g ?d?d?d?d): ")
    elif opt in ("-w", "--wordlist"):
        wordlist = arg
        while not check_file_presence(wordlist):
            print("Error: The wordlist you specified does not exist.")
            wordlist = input("Please enter a wordlist (e.g /home/user/rockyou.txt): ")
    elif opt in ("-o", "--outputFile"):
        output_file = arg
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
    session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
except:
    print("Error: Your credentials are invalid. Run --setup again if your credentials have changed.")
    exit()

config = get_config()

hashes = []

if hash_file == None and user_hash == None:
    _hash = input("Enter the hash you want to crack: ")
    _hash.strip("\n")
    _hash.strip()
    hashes.append(_hash)
elif (user_hash != None):
    user_hash.strip("\n")
    user_hash.strip()
    hashes.append(user_hash)
else:
    try:
        with open(hash_file, "r") as f:
            hashes = f.readlines() 
    except:
        print("Error: The file you specified does not exist. Please make sure you have entered the correct path.")
        exit()
    
    processed_hashes = []
    for _hash in hashes:
        _hash = _hash.strip()
        if _hash != "":
            processed_hashes.append(_hash)
    hashes = processed_hashes

sqs = session.resource('sqs')
delivery_queue = sqs.create_queue(QueueName='deliveryQueue.fifo', Attributes={'DelaySeconds': '1', 'FifoQueue': 'true'})
control_queue = sqs.create_queue(QueueName='controlQueue.fifo', Attributes={'DelaySeconds': '1', 'FifoQueue': 'true'})
return_queue = sqs.create_queue(QueueName='returnQueue.fifo', Attributes={'DelaySeconds': '1', 'FifoQueue': 'true'})

if len(hashes) == 0:
    print("Error: You have not entered any hashes to crack. Please try again.")
    cleanup()
else:
    ec2 = session.resource('ec2')
    hashing_instance = ec2.create_instances(ImageId=config["AWS-Settings"]["image_id"], MinCount=1, MaxCount=1, 
                                            InstanceType=config["AWS-Settings"]["instance_type"])
    print("Instance Created. Waiting for instance to be ready...")
    hashing_instance[0].wait_until_running()

    job_handler = JobHandler(delivery_queue, control_queue, return_queue)

    for _hash in hashes:
        if attack_type == "dictionary" or attack_type == "0":
            hash_job = job_handler.create_job(_hash, hash_type, attack_mode=attack_type, required_info={"wordlist": "Wordlist Goes Here"})
        elif attack_type == "mask" or attack_type == "3":
            hash_job = job_handler.create_job(_hash, hash_type, attack_mode=attack_type, required_info=mask)

        print(hash_job) ## DEBUG
        print(hash_job.to_json()) ## DEBUG
        job_handler.send_job(hash_job)


try:
    while True:
        signal.signal(signal.SIGINT, signal_handler)
        time.sleep(5)
        
        new_message = job_handler.check_for_response()
        status = None
        returned_job = None
        if new_message != None:
            try:
                returned_job = job_handler.load_from_json(new_message.body)
            except Exception as e:
                status = json.loads(new_message.body)
            
        if status != None:
            print(f"Status of {status['job_id']}: {status['progress']}") ## DEBUG
            ## Need to add progress bar here
        elif returned_job != None:
            print(f"Returned Job: {returned_job}")
            if returned_job.job_status == STATUS.COMPLETED:
                job_handler.delete_job(returned_job)
                print(f"Job {returned_job.job_id} completed. The result is {returned_job.required_info}") ## DEBUG
            elif returned_job.job_status == STATUS.FAILED:
                job_handler.delete_job(returned_job)
                print(f"Job {returned_job.job_id} failed. The error message is {returned_job.required_info}") ## DEBUG
            elif returned_job.job_status == STATUS.CANCELLED:
                job_handler.delete_job(returned_job)
                print(f"Job {returned_job.job_id} was sucessfully canceled.") ## DEBUG
            elif returned_job.job_status == STATUS.EXHAUSTED:
                job_handler.delete_job(returned_job)
                print(f"Job {returned_job.job_id} was not in the wordlist or mask you provided.") ## DEBUG
            
except KeyboardInterrupt:
    pass
except Exception as e:
    cleanup()
    raise e

