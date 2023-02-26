#from sh import hashcat
import boto3
import time
from cat_handler import HashcatHandler
import sys
sys.path.insert(0, "../")
from job_handler import STATUS


### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4

## Check For Two aws SQS Queues and assign them to variables
def get_infrastructure():
    sqs = boto3.resource('sqs')
    delivery = sqs.get_queue_by_name(QueueName='deliveryQueue.fifo')
    control = sqs.get_queue_by_name(QueueName='controlQueue.fifo')
    return_queue = sqs.get_queue_by_name(QueueName='returnQueue.fifo')
    return delivery, control, return_queue

## Check for messages in the delivery queue
def check_queue(queue):
    messages = queue.receive_messages(MaxNumberOfMessages=1)
    if len(messages) > 0:
        return messages[0]
    return None

# def load_job(job, job_queue):
#     # job_as_command
#     if job_queue.len() == 0:
#         hashcat('-a', job.attack_mode, '-m', job.hash_type, job.hash, job.required_info, '-w', '4')
#     else:
#         job_queue.append(job)

def complete_job_test(job): ### For testing message responses between consumer and producer
    print("Job Complete")
    job.job_status = STATUS.COMPLETED
    job.required_info = {"hash": job.hash, "dehashed": "password"}
    return job


## Send a message to the control queue



def main():
    delivery, control, return_queue = get_infrastructure()
    cat_handler = HashcatHandler(return_queue, control, delivery)
    print("Receiver is running...")
    while True:

        new_commands = check_queue(control)
        print("Checking for new commands...")

        if new_commands != None:
            for command in new_commands:
                print(command.body)
                command.delete()
        
        new_job = check_queue(delivery)
        print("Checking for new jobs...")
        if new_job != None:
            print("New job found!")
            job = cat_handler.load_from_json(new_job.body)
            print(job.to_json())
            new_job.delete()
            time.sleep(5)
            comp_job = complete_job_test(job)
            print("Returning Job")
            cat_handler.return_job(comp_job)
            time.sleep(1)
        time.sleep(5)

main()