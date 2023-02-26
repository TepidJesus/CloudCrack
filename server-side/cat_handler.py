## A modified version of the JobHandler class from job_handler.py:
#from sh import hashcat
import sys
sys.path.insert(0, "../")
from job_handler import JobHandler, Job, STATUS, Command, REQUEST
from sh import hashcat



class HashcatHandler(JobHandler):
    
        def __init__(self, outbound_queue, control_queue, inbound_queue):
            super().__init__(outbound_queue, control_queue, inbound_queue)
            self.hashcat_status = 0
            self.running = False
        
        def create_job(self, _hash, hash_type, attack_mode, required_info):
            raise NotImplementedError("This method is not implemented for HashcatHandler")
        
        def cancel_job(self, job):
            self.job_log[job.job_id].job_status = STATUS.CANCELLED
            self.return_job(job)

        def get_job_status(self, job):
            return self.job_log[job.job_id].job_status
    
        def check_for_response(self):
            messages = self.inbound_queue.receive_messages(MaxNumberOfMessages=10)
            if len(messages) > 0:
                return messages
            else:
                return None
    
        def load_job(self, job): 
            job_as_command = hashcat('-a', job.attack_mode, '-m', job.hash_type, job.hash, job.required_info, '-w', '4')
            if len(self.hashcat_queue) == 0:
                job_as_command()
                job.status = STATUS.RUNNING
                self.hashcat_status = 1
            else:
                self.hashcat_queue.append(job)


        def load_job_test(self):
            if self.running:
                return
            else:
                self.running = True
                hashcat('-a', 3, '-m', 0, "cc3a0280e4fc1415930899896574e118", "?l?l?l?l", '-w', '4')
 

        def job_complete(self, job):
            self.job_log[job.job_id].job_status = STATUS.COMPLETE
            self.return_job(job)

        def return_job(self, job):
            self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="1", MessageDeduplicationId=str(job.job_id))





