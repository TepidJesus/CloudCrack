import json
### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4

class STATUS:
    CREATED = 1,
    RUNNING = 2,
    COMPLETED = 3,
    FAILED = 4,
    CANCELLED = 5,
    SENT = 6
    PENDING = 7,
    EXHAUSTED = 8

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
    
class JobHandler:

    def __init__(self, outbound_queue, control_queue, inbound_queue):
        self.outbound_queue = outbound_queue
        self.control_queue = control_queue
        self.inbound_queue = inbound_queue

        self.job_id = 1
        self.job_log = {}

    def send_job(self, job):
        job.job_status = STATUS.SENT
        self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="Job", MessageDeduplicationId=str(job.job_id))

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
        messages = self.inbound_queue.receive_messages(MaxNumberOfMessages=1)
        if len(messages) > 0:
            messages[0].delete()
            return messages[0]
        else:
            return None
        
    def load_from_json(self, json_string):
        json_string = self.from_json(json_string)
        job = Job(int(json_string["job_id"]), json_string["hash"], json_string["hash_type"], self.convert_status(json_string["job_status"]), json_string["attack_mode"], json_string["required_info"])
        return job
    
    def convert_status(self, status):
        if status == "1":
            return STATUS.CREATED
        elif status == "2":
            return STATUS.RUNNING
        elif status == "3":
            return STATUS.COMPLETED
        elif status == "4":
            return STATUS.FAILED
        elif status == "5":
            return STATUS.CANCELLED
        elif status == "6":
            return STATUS.SENT
        elif status == "7":
            return STATUS.PENDING
        elif status == "8":
            return STATUS.EXHAUSTED
        else:
            return None

    def delete_job(self, job):
        del self.job_log[job.job_id]

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
    
    
        
        
    




        