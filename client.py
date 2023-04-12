from job_handler import JobHandler, STATUS
import boto3
from botocore.exceptions import ClientError
import json
import dotenv
import os
import sys

## Problems:
# - No status response after reciever crashes

## TODO: Make an AWS handler class that handles all AWS interactions to abstract away the boto3 API
## TODO: Finish settings menu and add a way to change settings and save them to the config file
## TODO: Add a way to check vCPU limit
## TODO: Add multi-instance support (Need a way to quantify the number of instances to the user)

class ClientController:

    def __init__(self):
        if not self.dotenv_present():
            self.run_setup()
        self.session = self.get_session()
        self.vCPU_limit = self.get_vCPU_count(self.session)
        if self.vCPU_limit < 4:
            
        self.job_handler = JobHandler(self.session, self.vCPU_limit)
        self.config = self.get_config()
        


    def run(self):
        self.print_welcome()
        while True:
            user_input = input("\nCloudCrack > ")
            self.job_handler.check_for_response()
            user_input.strip()
            input_as_list = user_input.split(" ")

            if input_as_list[0] == "help":
                self.print_help()
            elif input_as_list[0] in ["exit", "close", "quit"]:
                self.job_handler.cancel_all_jobs()
                break
            elif input_as_list[0] == "show":
                if len(input_as_list) < 2:
                    print("Use 'show all' to show all jobs or 'show <job_id>' to show a specific job")
                    continue 
                if input_as_list[1] == "all":
                    self.show_current_jobs()
                else:
                    try:
                        job_id = int(input_as_list[1])
                        self.show_current_job(job_id)
                    except:
                        print("Invalid Job ID")
            elif input_as_list[0] == "create":
                self.create_screen()
            elif input_as_list[0] == "cancel":
                if (len(input_as_list) == 2):
                    if input_as_list[1] == "all":
                        self.job_handler.cancel_all_jobs()
                    try:
                        job_id = int(input_as_list[1])
                        self.job_handler.cancel_job(job_id)
                    except:
                        print("Invalid Job ID")
                else:
                    job_id = int(input("Job ID: "))
                    try: 
                        self.job_handler.cancel_job(job_id)
                    except:
                        print("Invalid Job ID")
        

    def print_welcome(self):
        print("ASCII Art Goes Here")
        print("Welcome to Cloud Crack")
        print("Type 'help' for a list of commands")

    def print_help(self):
        print("\nhelp - print this message")
        print("exit - exit the program")
        print("show <all/job_id) - list all jobs or show a specific job")
        print("create - create a new job")
        print("options - show CloudCrack settings menu")
        print("cancel <job_id> - cancel a job")

    
    def show_current_jobs(self):
        print("Current Jobs:")
        for job_id in self.job_handler.job_log.keys():
            job = self.job_handler.get_job(job_id)
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job.hash)
            print("Status: " + job.job_status.name)
            if job.job_status == STATUS.RUNNING:
                print("Progress: " + str(round(job.progress[0] / job.progress[1], 2) * 100) + "%")
            elif job.job_status == STATUS.COMPLETED:
                print("Result: " + job.required_info)
            print("---------------------------------")

    def show_current_job(self, job_id):
        try:
            job = self.job_handler.get_job(job_id)
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job.hash)
            print("Status: " + job.job_status.name)
            if job.job_status == STATUS.RUNNING:
                print("Progress: " + str(round(job.progress[0] / job.progress[1], 2) * 100) + "%")
            elif job.job_status == STATUS.COMPLETED:
                print("Result: " + job.required_info)
            print("---------------------------------")
        except:
            raise Exception("Invalid Job ID")

    def create_screen(self):
        user_input = ""
        _hash = ""
        hash_type = ""
        attack_mode = ""
        mask = ""
        dictionary = ""
        output_file = ""
        hash_file_location = ""
        
        while user_input != "back" and user_input != "exit":
            user_input = input("\nCloudCrack > Create > ")
            input_as_list = user_input.split(" ")

            if input_as_list[0].lower() == "options" or input_as_list[0].lower() == "help":
                print("Options:")
                print("Hash: " + _hash)
                print("Hash Type: " + hash_type)
                print("Attack Mode: " + attack_mode)
                print("Mask: " + mask)
                print("Dictionary: " + dictionary)
                print("Output File (Optional): " + output_file)
                print("Hash File Location (Optional): " + hash_file_location)

            if input_as_list[0].lower() == "set":
                if input_as_list[1].lower() == "hash":
                    _hash = input_as_list[2].strip()
                elif input_as_list[1].lower() == "type":
                    hash_type = input_as_list[2].strip()
                elif input_as_list[1].lower() == "mode":
                    if (input_as_list[2].lower() not in ["0", "3", "dictionary", "mask"]):
                        print("Invalid attack mode")
                        continue
                    else:
                        if input_as_list[2].lower() == "dictionary":
                            attack_mode = "0"
                        elif input_as_list[2].lower() == "mask":
                            attack_mode = "3"
                        else:
                            attack_mode = input_as_list[2].strip()
                elif input_as_list[1].lower() == "mask":
                    mask = input_as_list[2].strip()
                elif input_as_list[1].lower() == "dictionary":
                    dictionary = input_as_list[2].strip()
                elif input_as_list[1].lower() == "output":
                    output_file = input_as_list[2].strip()
                elif input_as_list[1].lower() == "hashes":
                    hash_file_location = input_as_list[2].strip()

            if input_as_list[0].lower() in ["run", "start", "create"]:
                if dictionary == "" and attack_mode == "0":
                    print("You must provide a dictionary for attack mode 0")
                    continue
                if mask == "" and attack_mode == "3":
                    print("You must provide a mask for attack mode 3")
                    continue
                if _hash == "" and hash_file_location == "":
                    print("You must provide a hash OR hash file location")
                    continue
                if hash_type == "":
                    print("You must provide a hash type")
                    continue
                if attack_mode == "":
                    print("You must provide an attack mode")
                    continue
                if not self.valid_mask(mask):
                    print("Invalid mask. See the HashCat wiki for help")
                    continue
                
                if dictionary != "":
                    required_info = dictionary
                elif mask != "":
                    required_info = mask
                
                if hash_file_location != "":
                    try:
                        with open(hash_file_location, "r") as file:
                            pass
                    except:
                        print("Failed to open hash file. Please check the file location and try again")
                        continue

                    with open(hash_file_location, "r") as file:
                        hashes = file.readlines()
                    for _hash in hashes:
                        _hash = _hash.strip(" ")
                        _hash = _hash.strip("\n")
                        try: 
                            jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
                            self.job_handler.send_job(jb)
                        except:
                            print("Failed to create job") # DEBUG
                            continue
                else:
                    jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
                    self.job_handler.send_job(jb)

                

            if input_as_list[0] == "clear":
                _hash = ""
                hash_type = ""
                attack_mode = ""
                mask = ""
                dictionary = ""
                output_file = ""
                hash_file_location = ""

        return
    
    def valid_mask(self, mask):
        if mask == None:
            return False
        
        if "?" not in mask:
            return False
        
        if len(mask) <= 1:
            return False
        
        for i in range(len(mask)):
            char = mask[i]
            if char != "?" and char != "d" and char != "l" and char != "u" and char != "s" and char != "a" and char != "h" and char != "H" and char != "b":
                return False
            if char == "?" and i % 2 != 0:
                return False
            if char != "?" and i % 2 == 0:
                return False
        return True
    
    def dotenv_present(self):
        try:
            with open(".env", "r") as f:
                dotenv = f.read()
            return True
        except:
            return False
        
    def set_credentials(self, aws_access_key_id, aws_secret_access_key):
        with open(".env", "w") as f:
            f.write("AWS_ACCESS_KEY_ID=" + aws_access_key_id)
            f.write("\nAWS_SECRET_ACCESS_KEY=" + aws_secret_access_key)
        
    def run_setup(self):
        print("It looks like this is your first time running this program.")
        print("Lets get started by setting up your AWS credentials. You can find these instructions for this in the setup guide in the README.md file.")

        while True:
            aws_access_key_id = input("Enter your AWS Access Key ID: ")
            aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
            print("Please wait while I validate your credentials...")

            
    def get_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except:
            print("Error: The config file does not exist. Did you delete it? Go get a new one from the repository, it's kind of important.")
            exit()
        return config
    
    
    def vcpu_limit_message(self, limit):
        print("It looks like your AWS account has a P-Instance vCPU limit of " + str(limit) + ".")
        print("To use CloudCrack, you need to increase this limit to at least 4. (>8 recommended)")
        print("You can apply for a limit increase here: https://console.aws.amazon.com/servicequotas/home?region=us-east-2#!/services/ec2/quotas/L-417A185B")



class AwsController:
    def __init__(self, aws_access_key_id, aws_secret_access_key, config):
            self.session = None
            self.config = config
            if self.test_connection(aws_access_key_id, aws_secret_access_key):
                self.session = self.get_session()
            else:
                print("Error: Failed to connect to AWS. Please check your credentials and try again.")
                exit()

            self.effective_vCPU_limit = self.get_effective_vCPU_limit() * self.config["AWS-Settings"]["usage_limit"]
    
    def test_connection(self, aws_access_key_id, aws_secret_access_key):
        try:
            client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
            client.run_instances(ImageId=self.config['AWS-Settings']["image_id"], MinCount=1, MaxCount=1, InstanceType='t2.micro', DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                print("Error: Your credentials are invalid. Please make sure you entered them correctly.")
                return False
            else:
                print("Success! Your credentials are valid.")
                self.set_credentials(aws_access_key_id, aws_secret_access_key)
                print("You're all set! Have fun, but remember to be safe and to only use this tool for legitimate purposes.")
                return True
        except:
             print("Sorry, there was an error validating your credentials. Check you have enabled the correct permissions.")
             return False
        
    def get_session(self):
        dotenv.load_dotenv()
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
        return session
    
    def get_vCPU_limit(self):
        quota_client = self.session.client('service-quotas')
        response = quota_client.get_service_quota(ServiceCode='ec2', QuotaCode='L-417A185B')
        return int(response['Quota']['Value'])
    
    def create_queue(self, queue_name):
        sqs = self.session.resource('sqs')
        queue = sqs.create_queue(QueueName=queue_name, Attributes={'DelaySeconds': '1', 
                                                           'FifoQueue': 'true', 
                                                           'ContentBasedDeduplication': 'true'})
        return queue
    
    def create_instance(self, image_id, instance_type):
        ec2 = self.session.resource('ec2')
        instance = ec2.create_instances(ImageId=image_id, MinCount=1, MaxCount=1, InstanceType=instance_type)
        return instance
    
    def get_recomended_instance_type(self):
        vCPU_limit = self.get_vCPU_limit()
        if vCPU_limit >= 96:
            return "p4d.24xlarge"
        elif vCPU_limit >= 64:
            return "p3.16xlarge"
        elif vCPU_limit >= 32:
            return "p3.8xlarge"
        elif vCPU_limit >= 8:
            return "p3.2xlarge"
        elif vCPU_limit >= 4:
            return "p2.xlarge"
        else:
            return "t2.micro"