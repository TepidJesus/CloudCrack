import boto3
import time
import os
import dotenv
from cat_handler import HashcatHandler
import sys
sys.path.insert(0, "../")
from job_handler import STATUS, REQUEST
import json
from client import AwsController

### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4

## TODO: Integrate new AWSController class into here.
def get_infrastructure(session):
    sqs = session.resource('sqs')
    delivery = sqs.get_queue_by_name(QueueName='deliveryQueue.fifo')
    control = sqs.get_queue_by_name(QueueName='controlQueue.fifo')
    return_queue = sqs.get_queue_by_name(QueueName='returnQueue.fifo')
    s3_client = session.client('s3')
    return delivery, control, return_queue, s3_client

## Check for messages in the delivery queue
def check_queue(queue):
    messages = queue.receive_messages(MaxNumberOfMessages=1)
    if len(messages) > 0:
        return messages[0]
    return None

def get_config():
    try:
        with open("../config.json", "r") as f:
            config = json.load(f)
    except:
        print("Error: The config file does not exist. Did you delete it? Go get a new one from the repository, it's kind of important.")
        exit()
    return config

def main():

    try:
        dotenv.load_dotenv()
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
    except:
        print("Error: Your credentials are invalid. Run --setup again if your credentials have changed.")
        exit()    

    delivery, control, return_queue, s3_client = get_infrastructure(session)
    cat_handler = HashcatHandler(AwsController(get_config()), "server")
    print("Receiver is running...")
    while True:

        command = check_queue(control)
        print("Checking for new commands...")

        if command != None:
            commandJs = json.loads(command.body)
            if commandJs["request"] == REQUEST.CANCEL:
                print("Cancel command received!")
                cat_handler.cancel_job(int(commandJs["job_id"]))
            command.delete()
        
        if cat_handler.current_job is None:
            new_job = check_queue(delivery)
            print("Checking for new jobs...")
            if new_job != None:
                print("New job found!")
                job = cat_handler.load_from_json(new_job.body)
                print(job.to_json())
                cat_handler.run_job(job)
                new_job.delete()
        time.sleep(5)

main()