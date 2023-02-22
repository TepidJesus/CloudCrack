import json
### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4

class STATUS:
    CREATED = 1,
    RUNNING = 2,
    FINISHED = 3,
    FAILED = 4,
    CANCELLED = 5,
    SENT = 6
    PENDING = 7

class Job:

    def __init__(self, job_id, _hash, hash_type, attack_mode, required_info):
        self.job_id = job_id
        self.hash = _hash
        self.hash_type = hash_type
        self.job_status = STATUS.CREATED
        self.attack_mode = attack_mode
        self.required_info = required_info

    def __str__(self):
        return f"Job ID: {self.job_id} | Hash: {self.hash} | Hash Type: {self.hash_type} | Job Status: {self.job_status}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def from_json(self, json_string):
        return json.loads(json_string)


class JobHandler:

    def __init__(self, outbound_queue, control_queue, inbound_queue):
        self.outbound_queue = outbound_queue
        self.control_queue = control_queue
        self.inbound_queue = inbound_queue

        self.job_id = 1
        self.job_log = {}

    def send_job(self, job):
        self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="1", MessageDeduplicationId=str(job.job_id))

    def get_new_job_id(self):
        num = self.job_id
        self.job_id += 1
        return num
    
    def create_job(self, _hash, hash_type, attack_mode, required_info):
        job = Job(self.get_new_job_id(), _hash, hash_type, attack_mode, required_info)
        self.job_log[job.job_id] = job
        return job
    
    def cancel_job(self, job):
        self.job_log[job.job_id].job_status = STATUS.CANCELLED
        self.control_queue.send_message(MessageBody=Command(job.job_id, REQUEST.CANCEL).to_json())
    
    def get_local_job_status(self, job):
        return self.job_log[job.job_id].job_status
    
    def request_job_status(self, job):
        self.control_queue.send_message(MessageBody=Command(job.job_id, REQUEST.STATUS).to_json())

    def check_for_response(self):
        messages = self.inbound_queue.receive_messages(MaxNumberOfMessages=10)
        if len(messages) > 0:
            return messages
        else:
            return None

class REQUEST:
    CANCEL = 1,
    STATUS = 2,
 

class Command:

    def __init__(self, job_id, request):
        self.job_id = job_id
        self.request = request

    def __str__(self):
        return f"Job ID: {self.job_id} | Job Status: {self.job_status}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def from_json(self, json_string):
        return json.loads(json_string)
    
        
        
    




        