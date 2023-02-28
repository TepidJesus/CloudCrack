## A modified version of the JobHandler class from job_handler.py:
#from sh import hashcat
import sys
sys.path.insert(0, "../")
from job_handler import JobHandler, Job, STATUS, Command, REQUEST
from sh import hashcat
from io import StringIO
import json



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
                
        def process_output(self, line):
            try:
                line_json = json.loads(line)
                print(f"Current Status: {line_json['status']}") 
                print(f"Progress: {int(line_json['progress'][0]) / int(line_json['progress'][1]) * 100:.2f}%")
            except:
                print("Has Found " + line.strip())


        def load_job_test(self):
            if self.running:
                return
            else:
                self.running = True
                job = hashcat('-a3','-m0', "909cc49a73e86ccac31c3f6d5c62c959", "?l?l?l?l?l?l?l?l", '-w4', "--status", "--quiet", "--status-json", _bg=True, _out=self.process_output, _ok_code=[0,1])
                job.wait()
 

        def job_complete(self, job):
            self.job_log[job.job_id].job_status = STATUS.COMPLETE
            self.return_job(job)

        def return_job(self, job):
            self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="1", MessageDeduplicationId=str(job.job_id))











