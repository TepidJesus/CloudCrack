## A modified version of the JobHandler class from job_handler.py:
#from sh import hashcat
import sys
sys.path.insert(0, "../")
from job_handler import JobHandler, Job, STATUS, Command, REQUEST
from sh import hashcat
import json
import sh
import os



class HashcatHandler(JobHandler): #TODO: Seperate this class from the JobHandler class and split mananging jobs and running jobs into two classes
    
        def __init__(self, outbound_queue, control_queue, inbound_queue, s3_client):
            super().__init__(outbound_queue, control_queue, inbound_queue)
            self.hashcat_status = 0
            self.current_job = None
            self.process = None
            self.s3_client = s3_client
        
        def create_job(self, _hash, hash_type, attack_mode, required_info):
            raise NotImplementedError("This method is not implemented for HashcatHandler")
        
        def cancel_job(self, job):
            if self.current_job is None:
                return
            elif self.current_job.job_id != job.job_id:
                return
            
            self.current_job.job_status = STATUS.CANCELLED
            try:
                self.process.kill()
            except sh.SignalException_SIGKILL: # When job is cancelled
                self.job_complete(self.current_job, "CANCELLED")
                
            self.current_job = None
            self.process = None

            print("Job cancelled")

            self.return_job(job)

        def get_job_status(self, job):
            return self.current_job.job_status

        # Get the wordlist from the S3 bucket
        def get_wordlist(self, bucket_name):
            self.s3_client.download_file(bucket_name, "UsersWordlist", "wordlist.txt")
            return os.getcwd() + "/wordlist.txt"

    
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
                    wrdlst = self.get_wordlist(job.required_info) # Need to add failure handling to return job as failed
                    print(wrdlst) #DEBUG
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
                    
            except sh.ErrorReturnCode: # When hashcat encounters an error that must be reported to dev
                self.job_complete(self.current_job, f"ERROR: {job.exit_code}")
            except Exception as e:
                print(e)

            
            

                
        def process_output(self, line):
            try:
                line_json = json.loads(line)
                # print(f"Current Status: {line_json['status']}") 
                # print(f"Progress: {int(line_json['progress'][0]) / int(line_json['progress'][1]) * 100:.2f}%\n")
                self.report_progress( int(line_json['progress'][0]) / int(line_json['progress'][1]) * 100)
                
                if line_json['status'] == 5:
                    self.job_complete(self.current_job, "EXHAUSTED")
                    return True
                
            except:
                print("Job completed")
                self.job_complete(self.current_job, line.split(":")[1])
                return True

            

        def report_progress(self, progress):
            print(f"Reporting progress: {progress:.2f}%")
            self.outbound_queue.send_message(MessageBody=json.dumps({"job_id": self.current_job.job_id, "progress": progress}), 
                                                                    MessageGroupId="Status", MessageDeduplicationId=str(self.current_job.job_id)+ str(progress))
 
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
            self.current_job = None
            self.process = None
            print(f"Job {job.job_id} completed with result: {result}")
            self.return_job(job)

        def return_job(self, job):
            print("Returning job")
            self.outbound_queue.send_message(MessageBody=job.to_json(), MessageGroupId="Job", MessageDeduplicationId=str(job.job_id) + str(job.job_status))