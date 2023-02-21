import json
### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4
class JobHandler:

    def __init__(self, delivery_queue, control_queue, return_queue):
        self.delivery_queue = delivery_queue
        self.control_queue = control_queue
        self.return_queue = return_queue

        self.job_id = 1
        self.job_log = {}

    def send_job(self, job):
        self.delivery_queue.send_message(MessageBody=job.to_json())

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
        self.control_queue.send_message(MessageBody=Command(job.job_id, STATUS.CANCELLED).to_json())
    
    def get_job_status(self, job):
        return self.job_log[job.job_id].job_status

    def check_for_response(self):
        messages = self.return_queue.receive_messages(MaxNumberOfMessages=10)
        if len(messages) > 0:
            return messages
        else:
            return None

class STATUS:
    CREATED = 1,
    RUNNING = 2,
    FINISHED = 3,
    FAILED = 4,
    CANCELLED = 5,
    SENT = 6
 
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
    
        
    




        