### HashCat Command Format: hashcat -a <attack_mode> -m <hash_type> <hash> <wordlist/mask/length> -w 4
class JobHandler:

    def __init__(self, delivery_queue, control_queue, return_queue):
        self.delivery_queue = delivery_queue
        self.control_queue = control_queue
        self.return_queue = return_queue

        self.job_log = {}

 
class Job:

    def __init__(self, job_id, _hash, wordlist, hash_type, attack_mode):
        self.job_id = job_id
        self.hash = _hash
        self.wordlist = wordlist
        self.hash_type = hash_type
        self.job_status = 'created'
        self.attack_mode = attack_mode

    def __str__(self):
        return f"Job ID: {self.job_id} | Hash: {self.hash} | Wordlist: {self.wordlist} | Hash Type: {self.hash_type} | Job Status: {self.job_status}"


        