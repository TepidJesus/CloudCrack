## A modified version of the JobHandler class from job_handler.py:
#from sh import hashcat
import sys
sys.path.insert(0, "../")
from job_handler import JobHandler, Job, STATUS, Command, REQUEST
from sh import hashcat
import json
from sh import ErrorReturnCode, SignalException_SIGKILL, SignalException_SIGSEGV
import os

## TODO: Integrate new AWSController class into here.

class HashcatHandler(JobHandler): #TODO: Seperate this class from the JobHandler class and split mananging jobs and running jobs into two classes
    
        # NEED TO REDO THIS TO ALIGN WITH THE NEW JOB HANDLER
        def __init__(self, aws_controller):
            super().__init__(aws_controller, "server")
            self.hashcat_status = 0
            self.current_job = None
            self.process = None
        
        def cancel_job(self, job_id):
            if self.current_job is None:
                return
            elif self.current_job.job_id != job_id:
                return
            
            self.current_job.job_status = STATUS.CANCELLED
            try:
                self.process.kill()
            except SignalException_SIGKILL: # When job is cancelled
                self.job_complete(self.current_job, "CANCELLED")
            
            job_tmp = self.current_job
            self.reset_job()

            print("Job cancelled")

            self.return_job(job_tmp)

        def reset_job(self):
            self.current_job = None
            self.process = None


        def get_wordlist(self, bucket_name, file_name):
            try:
                self.s3_client.download_file(bucket_name, "UsersWordlist", file_name)
            except Exception as e:
                print(f"Error: Failed to download wordlist from S3 bucket {bucket_name}. Continuing...")
                return None
            return os.getcwd() + "/" + file_name + ".txt"

    
        def check_for_response(self):
            messages = self.inbound_queue.receive_messages(MaxNumberOfMessages=1)
            if len(messages) > 0:
                return messages
            else:
                return None
    
        def run_job(self, job):
            if self.current_job is not None:
                return
            
            job.job_status = STATUS.RUNNING
            self.current_job = job

            print("Job started")

            try:
                if job.attack_mode == "0":
                    wrdlst = self.get_wordlist(job.required_info[1], job.required_info[0]) # Need to add failure handling to return job as failed
                    if wrdlst is None:
                        self.job_complete(self.current_job, "ERROR: Failed to download wordlist from S3 bucket")
                        return
                    job_as_command = hashcat(f'-a0', f'-m{job.hash_type}', job.hash, wrdlst, 
                                            '-w4', "--status", "--quiet", "--status-json", _bg=True, 
                                            _out=self.process_output, _ok_code=[0,1])
                    self.process = job_as_command                           
                elif job.attack_mode == "3":
                    job_as_command = hashcat(f'-a3', f'-m{job.hash_type}', job.hash, job.required_info, 
                                            '-w4', "--status", "--quiet", "--status-json", _bg=True, 
                                            _out=self.process_output, _ok_code=[0,1])
                    self.process = job_as_command
                else:
                    print("Invalid attack mode")
                    return
                
            except ErrorReturnCode: # When hashcat encounters an error that must be reported to dev
                self.job_complete(self.current_job, f"ERROR: {job_as_command.exit_code}")
                self.reset_job()
            except SignalException_SIGSEGV:
                print("Error: Hashcat encountered a fatal error")
                self.job_complete(self.current_job, "ERROR: Hashcat encountered a fatal error")
                self.reset_job()
                return
            except Exception as e:
                print("Error: Failed to run job")
                self.job_complete(self.current_job, "ERROR: Unknown error")
                self.reset_job()
                return
               
        def process_output(self, line):
            try:
                line_json = json.loads(line)
                if line_json['status'] == 5:
                    self.job_complete(self.current_job, "EXHAUSTED")
                    return True
                
                self.report_progress(int(line_json['progress'][0]), int(line_json['progress'][1]))
                 
            except Exception as e:
                print("Job completed")
                self.job_complete(self.current_job, line.split(":")[1].strip('\n'))
                return True

            

        def report_progress(self, current, total):
            self.aws_controller.send_message(json.dumps({"job_id": self.current_job.job_id, 
                                                                    "current": current, 
                                                                    "total": total}), 
                                                                    "Status")
 
        def job_complete(self, job, result):
            if result == "EXHAUSTED":
                job.job_status = STATUS.EXHAUSTED
                result = ""
            elif result[:5] == "ERROR":
                job.job_status = STATUS.FAILED
                result = result[6:]
            elif result == "CANCELLED":
                job.job_status = STATUS.CANCELLED
                result = ""
            else:
                job.job_status = STATUS.COMPLETED
            job.required_info = result
            self.reset_job()
            print(f"Job {job.job_id} completed with result: {result}")
            self.return_job(job)

        def return_job(self, job):
            print("Returning job")
            self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="Job")