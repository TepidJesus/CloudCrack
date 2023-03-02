## A modified version of the JobHandler class from job_handler.py:
#from sh import hashcat
import sys
sys.path.insert(0, "../")
from job_handler import JobHandler, Job, STATUS, Command, REQUEST
from sh import hashcat
import json



class HashcatHandler(JobHandler):
    
        def __init__(self, outbound_queue, control_queue, inbound_queue):
            super().__init__(outbound_queue, control_queue, inbound_queue)
            self.hashcat_status = 0
            self.current_job = None
            self.process = None
        
        def create_job(self, _hash, hash_type, attack_mode, required_info):
            raise NotImplementedError("This method is not implemented for HashcatHandler")
        
        def cancel_job(self, job):
            if self.current_job is None:
                return
            elif self.current_job.job_id != job.job_id:
                return
            
            self.current_job.job_status = STATUS.CANCELLED
            self.process.kill()
            self.current_job = None
            self.process = None
            
            self.return_job(job)

        def get_job_status(self, job):
            return self.current_job.job_status
    
        def check_for_response(self):
            messages = self.inbound_queue.receive_messages(MaxNumberOfMessages=10)
            if len(messages) > 0:
                return messages
            else:
                return None
    
        def run_job(self, job):
            if self.current_job is not None:
                return
            
            job.job_status = STATUS.RUNNING
            self.current_job = job
            try:
                if job.attack_mode == "mask":
                    job_as_command = hashcat(f'-a3', f'-m{job.hash_type}', job.hash, job.required_info, 
                                            '-w4', "--status", "--quiet", "--status-json", _bg=True, 
                                            _out=self.process_output, _ok_code=[0,1])
                                            
                elif job.attack_mode == "dictionary":
                    job_as_command = hashcat(f'-a0', f'-m{job.hash_type}', job.hash, job.required_info, 
                                            '-w4', "--status", "--quiet", "--status-json", _bg=True, 
                                            _out=self.process_output, _ok_code=[0,1])
                    
                self.process = job_as_command

            except hashcat.ErrorReturnCode_1: # When hashcat could exhaust the dictionary or mask
                self.job_complete(self.current_job, "EXHAUSTED")
            except hashcat.ErrorReturnCode: # When hashcat encounters an error that must be reported to dev
                self.job_complete(self.current_job, f"ERROR: {job.exit_code}")

            job_as_command.wait()
            self.current_job = None
            self.process = None

                
        def process_output(self, line):
            try:
                line_json = json.loads(line)
                print(f"Current Status: {line_json['status']}") 
                print(f"Progress: {int(line_json['progress'][0]) / int(line_json['progress'][1]) * 100:.2f}%\n")
                self.report_progress(line_json['status'], int(line_json['progress'][0]) / int(line_json['progress'][1]) * 100)
            except:
                self.job_complete(self.current_job, line.split(":")[1])
                return True

        def report_progress(self, current_status, progress):
            print(f"Reporting progress: {progress:.2f}%")
            self.outbound_queue.send_message(MessageBody=json.dumps({"job_id": self.current_job.job_id, "current_status": current_status, "progress": progress}), 
                                                                    MessageGroupId="Status")
 
        def job_complete(self, job, result):
            if result == "EXHAUSTED":
                job.job_status = STATUS.EXHAUSTED
            elif result[:5] == "ERROR":
                job.job_status = STATUS.FAILED
                result = result[6:]
            else:
                job.job_status = STATUS.COMPLETED
            job.required_info = result
            print(f"Job {job.job_id} completed with result: {result}")
            self.return_job(job)

        def return_job(self, job):
            print("Returning job")
            self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="Job")