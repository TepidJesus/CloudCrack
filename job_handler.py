import json
import boto3
import uuid
from enum import Enum, IntEnum
### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4

class STATUS(IntEnum):
    CREATED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5
    QUEUED = 6
    PENDING = 7
    EXHAUSTED = 8

class Job:

    def __init__(self, job_id, _hash, hash_type, status, attack_mode, required_info, result_file=None):
        self.job_id = job_id
        self.hash = _hash
        self.hash_type = hash_type
        self.job_status = status
        self.attack_mode = attack_mode
        self.required_info = required_info
        self.progress = [0,0]
        self.result_file = result_file

    def __str__(self):
        return f"Job ID: {self.job_id} | Hash: {self.hash} | Hash Type: {self.hash_type} | Job Status: {self.job_status}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
class JobHandler:

    def __init__(self, session):
        self.s3_client = session.client('s3')
        self.sqs_client = session.resource('sqs')
        self.outbound_queue = self.sqs_client.create_queue(QueueName='deliveryQueue.fifo', 
                                               Attributes={'DelaySeconds': '1', 
                                                           'FifoQueue': 'true', 
                                                           'ContentBasedDeduplication': 'true'})
        self.control_queue = self.sqs_client.create_queue(QueueName='controlQueue.fifo', 
                                              Attributes={'DelaySeconds': '1', 
                                                          'FifoQueue': 'true', 
                                                          'ContentBasedDeduplication': 'true'})
        self.inbound_queue = self.sqs_client.create_queue(QueueName='returnQueue.fifo', 
                                              Attributes={'DelaySeconds': '1', 
                                                          'FifoQueue': 'true', 
                                                          'ContentBasedDeduplication': 'true'})
        self.job_id = 1
        self.job_log = {}

    def send_job(self, job):
        job.job_status = STATUS.QUEUED
        if job.required_info is not None and job.attack_mode == 0:
            response = self.create_bucket(job.required_info)
            if response == None:
                job.job_status = STATUS.FAILED
                return
            else:
                job.required_info = response
        response = self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="Job")
        self.job_log[job.job_id] = (job, response['ReceiptHandle']) 

    def get_new_job_id(self):
        num = self.job_id
        self.job_id += 1
        return num
    
    def create_job(self, _hash, hash_type, attack_mode, required_info):
        job = Job(self.get_new_job_id(), _hash, hash_type, STATUS.CREATED, attack_mode, required_info)
        return job
    
    def get_job(self, job_id):
        return self.job_log[job_id][0]
    
    def cancel_job(self, job_id):
        self.job_log[job_id].job_status[0] = STATUS.CANCELLED
        self.control_queue.send_message(MessageBody=Command(job_id, REQUEST.CANCEL).to_json(), MessageGroupId="Command")

    def cancel_all_jobs(self):
        for job in self.job_log:
            self.cancel_job(job)
    
    def get_local_job_status(self, job):
        return self.job_log[job.job_id][0].job_status

    def check_for_response(self):
        inboundMessages = self.inbound_queue.receive_messages(MaxNumberOfMessages=10)

        if len(inboundMessages) > 0:
            for message in inboundMessages:
                try:
                    job = self.load_from_json(message.body)
                    self.job_log[job.job_id][0] = job
                    if job.job_status == STATUS.COMPLETED and job.result_file is not None:
                        self.update_result_file(job)
                except Exception as e:
                    status = json.loads(message.body)
                    self.job_log[status["job_id"]][0].progress[0] = status["current"]
                    self.job_log[status["job_id"]][0].progress[1] = status["total"]
                    self.job_log[status["job_id"]][0].job_status = STATUS.RUNNING
                message.delete()
        
    def from_json(self, json_str):
        return json.loads(json_str)
        
    def load_from_json(self, json_string):
        json_string = self.from_json(json_string)
        job = Job(int(json_string["job_id"]), json_string["hash"], json_string["hash_type"], self.convert_status(json_string["job_status"]), json_string["attack_mode"], json_string["required_info"])
        return job
    
    def update_result_file(self, job):
        with open(job.result_file, "w") as f:
            strng = f"{job.hash} : {job.required_info}"
            f.write(strng)

    def create_bucket(self, wordlist_file):
        bucket_name = ''.join(["list_bucket", str(uuid.uuid4())])
        wordlist_bucket = self.s3_client.create_bucket(
             Bucket=bucket_name,
             CreateBucketConfiguration={
             'LocationConstraint': "us-east-2"})
        try:
            response = self.s3_client.upload_file(wordlist_file, bucket_name, "UsersWordlist")
            return bucket_name
        except Exception as e:
            print("Failed to upload wordlist to S3. Check the file path and try again.")
            return None
        
    
    def convert_status(self, status):
        if status == 1:
            return STATUS.CREATED
        elif status == 2:
            return STATUS.RUNNING
        elif status == 3:
            return STATUS.COMPLETED
        elif status == 4:
            return STATUS.FAILED
        elif status == 5:
            return STATUS.CANCELLED
        elif status == 6:
            return STATUS.QUEUED
        elif status == 7:
            return STATUS.PENDING
        elif status == 8:
            return STATUS.EXHAUSTED
        else:
            return None

    def delete_job(self, job):
        del self.job_log[job.job_id]

class REQUEST(IntEnum):
    CANCEL = 1
    STATUS = 2
 

class Command:

    def __init__(self, job_id, request):
        self.job_id = job_id
        self.request = request

    def __str__(self):
        return f"Job ID: {self.job_id} | Job Status: {self.job_status}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    
        
        
    




        