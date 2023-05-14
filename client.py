from job_handler import JobHandler, STATUS
import boto3
from botocore.exceptions import ClientError
import json
import dotenv
import os
import time
import uuid

## Problems:

## TODO: Finish settings menu and add a way to change settings and save them to the config fil
## TODO: Potentially add a seperate control queue for each Ec2 hashing instance
## TODO: Make it so client doens't cry if the queues already exist when it tries to create them

#### Saturday TO DO ####
## TODO: Add IAM priviledges to the IAM role
## TODO: EC2 Instance Creation, IAM Role Assignemnt
## TODO: Add EC2 auto start and stop based on load

class ClientController:

    def __init__(self):
        self.aws_controller = AwsController(self.get_config(), "client")
        self.job_handler = JobHandler(self.aws_controller, "client")
        
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
                self.aws_controller.cleanup()
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
            else:
                print("Unknown Command -- Type 'help' for a list of commands")
        

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
                print("Attack Mode: " + str(attack_mode))
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
                            attack_mode = 0
                        elif input_as_list[2].lower() == "mask":
                            attack_mode = 3
                        else:
                            attack_mode = int(input_as_list[2].strip())
                elif input_as_list[1].lower() == "mask":
                    mask = input_as_list[2].strip()
                elif input_as_list[1].lower() == "dictionary":
                    dictionary = input_as_list[2].strip()
                elif input_as_list[1].lower() == "output":
                    output_file = input_as_list[2].strip()
                elif input_as_list[1].lower() == "hashes":
                    hash_file_location = input_as_list[2].strip()
                else:
                    print("Invalid option -- Type 'help' for a list of options")

            if input_as_list[0].lower() in ["run", "start", "create"]:
                if dictionary == "" and attack_mode == 0: 
                    print("You must provide a dictionary for attack mode 0") 
                    continue
                if mask == "" and attack_mode == 3:
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
                if attack_mode == 3 and not self.valid_mask(mask):
                    print("Invalid mask. See the HashCat wiki for help")
                    continue
                
                if dictionary != "":
                    try:
                        with open(dictionary, "r") as file:
                            required_info = dictionary
                            pass
                    except:
                        print("Failed to open dictionary file. Please check the file location and try again")
                        continue
           
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
    def __init__(self, config, mode):
            self.credentialManager = self.CredentialManager(self)
            self.session = None
            self.config = config
            self.instances = []
            self.instance_profile = None
            
            if mode == "client":
                if self.test_ec2(self.credentialManager.get_aws_access_key_id(), self.credentialManager.get_aws_secret_access_key()):
                    self.session = self.get_session("client")
                else:
                    exit()
                if not self.test_sqs() and not self.test_s3():
                    exit()
                
                self.effective_vCPU_limit = self.get_vCPU_limit() * int(self.config["AWS-Settings"]["usage_limit"])
                self.instance_config = self.get_recomended_instance_config()
            elif mode == "server":
                self.session = self.get_session("server")


    
    def test_ec2(self, aws_access_key_id, aws_secret_access_key):
        try:
            client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
            client.run_instances(ImageId=self.config['AWS-Settings']["image_id"], MinCount=1, MaxCount=1, InstanceType='t2.micro', DryRun=True)
            return True  
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: EC2 Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
            elif 'DryRunOperation' not in str(e):
                print("Error: Your credentials are invalid. Please make sure you entered them correctly.")
                return False
            elif 'DryRunOperation' in str(e):
                return True

        
    def test_s3(self):
        try:
            s3 = self.session.client('s3')
            s3.list_buckets(DryRun=True)
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: S3 Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
            elif 'DryRunOperation' in str(e):
                    return True
            else:
                print("S3 Test Error") ## DEBUG
                return False
    
    def test_sqs(self):
        try:
            sqs = self.session.resource('sqs')
            queue = sqs.create_queue(QueueName="test.fifo", Attributes={'DelaySeconds': '1', 
                                                            'FifoQueue': 'true', 
                                                            'ContentBasedDeduplication': 'true'})
            queue.delete()
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: SQS Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
            else:
                print(e)


        print("SQS Test Error") ## DEBUG
        return False
        
    def get_session(self, mode):
        if mode == "client":
            dotenv.load_dotenv()
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            session = boto3.Session(aws_access_key_id=aws_access_key_id, 
                                    aws_secret_access_key=aws_secret_access_key, 
                                    region_name='us-east-2')
        else:
            session = boto3.Session(region_name='us-east-2')
        return session
    
    def get_vCPU_limit(self):
        quota_client = self.session.client('service-quotas')
        response = quota_client.get_service_quota(ServiceCode='ec2', QuotaCode='L-417A185B')
        print(f"Your current vCPU limit is {response['Quota']['Value']}") ## DEBUG
        return int(response['Quota']['Value'])
    
    def get_instances(self):
        return self.instances
    
    def create_queue(self, queue_name):
        sqs = self.session.resource('sqs')
        print("Creating queue: " + queue_name + ".fifo") ## DEBUG
        try:
            queue = sqs.create_queue(QueueName=queue_name + ".fifo", Attributes={'DelaySeconds': '1', 
                                                            'FifoQueue': 'true', 
                                                            'ContentBasedDeduplication': 'true'})
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.QueueDeletedRecently':
                print("Error: Looks like you restarted CloudCrack to quickly and made AWS mad. Please wait a 60 seconds and try again.")
                exit()
            elif e.response['Error']['Code'] == 'AWS.SimpleQueueService.QueueNameExists':
                print(f"Error: Looks like you already have a queue with the name {queue_name}. If you made this queue yourself, please delete or rename it and try again.")
                exit()
            else:
                print(e)
        except Exception as e:
            print("Error: Failed to create queue. Please check your AWS credentials and try again.")
            print(e) ## DEBUG
            self.cleanup()
            exit()
        return queue
    
    def message_queue(self, queue, message_body, message_type): ## TODO: FINISH ERROR HANDLING
        try:
            response = queue.send_message(MessageBody=message_body, MessageGroupId=message_type)
            return response
        except ClientError as e:
            if self.test_sqs():
                for i in range(3):
                    response = queue.send_message(MessageBody=message_body, MessageGroupId=message_type)
                    if response:
                        return response
                    else:
                        print(f"Error: Failed to send message to the queue. Retrying... {3 - i} attempts left.")
                        time.sleep(5)
                        return False
            if message_type == "Job":
                print(f"Error: Failed to send Job {message_body['job_id']} to the queue.")
            else:
                print(f"Error: Failed to send {message_type} to the queue.")
            return False
        
    def locate_queue(self, name):
        sqs = self.session.resource('sqs')
        try:
            queue = sqs.get_queue_by_name(QueueName=name + ".fifo")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                print(f"Error: Failed to locate queue: {name}.fifo")
                return
        return queue
    
    def create_instance(self):
        ec2 = self.session.resource('ec2')
        print("Creating instance...") ## DEBUG
        if self.instance_profile is None:
            self.instance_profile = self.create_instance_profile()
        try:
            instance = ec2.create_instances(ImageId=self.config["AWS-Settings"]["image_id"], 
                                            MinCount=1, 
                                            MaxCount=1, 
                                            InstanceType=self.instance_config[0], IamInstanceProfile={'Arn': self.instance_profile})
            self.instances.append(instance[0])
        except ClientError as e:
            if e.response['Error']['Code'] == 'InsufficientInstanceCapacity':
                print("Error: Failed to create instances. Looks like those pesky ML engineers are using all the GPU instances.")
                if len(instance) == 0:
                    print("Please try again later or try a different region. (Specify this in config.json file)")
                else:
                    print(f"Only Secured {self.get_num_instances()}. You can continue with this number of instances, but you will experience decreased performance.")
                    print("You can also try again later or try a different region. (Specify this in the settings menu)")
            elif e.response['Error']['Code'] == 'VcpuLimitExceeded':
                print("VCPU Limit Exceeded") ## DEBUG
                return
            else:
                print(e)
        except Exception as e:
            print(e)

    
    def create_bucket(self, bucket_prefix):
        s3 = self.session.client('s3')
        bucket_name = self.create_bucket_name(bucket_prefix)
        try:
            bucket = s3.create_bucket(Bucket=bucket_name, 
                                      CreateBucketConfiguration={'LocationConstraint': "us-east-2"})
        except:
            print("Error: Failed to create bucket. Please check your AWS credentials and try again.") ## TODO: NEED MORE SPECIFIC ERROR HANDLING
            return False ## TODO: Raise exception instead of returning False
        return bucket_name
    
    def upload_file(self, file_path, bucket_name, file_name):
        try:
            self.session.client('s3').upload_file(file_path, bucket_name, file_name)
        except ClientError as e:
            print("Error: Failed to upload file. Please check your AWS credentials and try again.") ## TODO: NEED MORE SPECIFIC ERROR HANDLING
            return False
        return True
    
    def download_file(self, bucket_name, file_name, local_name):
        try:
            self.session.client('s3').download_file(bucket_name, file_name, local_name)
            return local_name
        except ClientError as e:
            print(e)
            print("Error: Failed to download file. Please check your AWS credentials and try again.")
    
    def create_bucket_name(self, bucket_prefix):
        return ''.join([bucket_prefix, str(uuid.uuid4())])
    
    def close_instances(self):
        ec2 = self.session.resource('ec2')
        for instance in self.instances:
            instance.terminate()

    def close_buckets(self):
        s3 = self.session.resource('s3')
        buckets = s3.buckets.all()
        for bucket in buckets:
            bucket.objects.all().delete()
            bucket.delete()
    
    def close_queues(self):
        sqs = self.session.resource('sqs')
        queues = sqs.queues.all()
        for queue in queues:
            print(f"Deleting queue: {queue.url}") ## DEBUG
            queue.delete()

    def remove_iam_role(self): ## TODO: Delete policies before deleting role
        iam = self.session.client('iam')
        roles = iam.list_roles()
        for role in roles['Roles']:
            if role['RoleName'] == 'CloudCrack-s3-sqs-role':
                iam.delete_role_policy(RoleName='CloudCrack-s3-sqs-role', PolicyName='s3-sqs-permissions')
                iam.delete_role(RoleName='CloudCrack-s3-sqs-role')
                return True
        return False
    
    
    def remove_instance_profile(self):
        iam = self.session.client('iam')
        profiles = iam.list_instance_profiles()
        for profile in profiles['InstanceProfiles']:
            if profile['InstanceProfileName'] == 'CloudCrack-s3-sqs-instance-profile':
                try:
                    iam.remove_role_from_instance_profile(InstanceProfileName='CloudCrack-s3-sqs-instance-profile', RoleName='CloudCrack-s3-sqs-role')
                except:
                    pass
                iam.delete_instance_profile(InstanceProfileName='CloudCrack-s3-sqs-instance-profile')
                return True
        return False

    def cleanup(self):
        self.close_instances()
        self.close_buckets()
        self.close_queues()
        self.remove_instance_profile()
        self.remove_iam_role()

    def get_num_instances(self):
        return len(self.instances)

    def get_max_instances(self):
        return self.instance_config[1]

    def get_recomended_instance_config(self): 
        if self.effective_vCPU_limit // 96 >=  1:
            return ("p4d.24xlarge", self.effective_vCPU_limit // 96)
        elif self.effective_vCPU_limit // 64 >= 1:
            return ("p3.16xlarge", self.effective_vCPU_limit // 64)
        elif self.effective_vCPU_limit // 32 >= 1:
            return ("p3.8xlarge", self.effective_vCPU_limit // 32)
        elif self.effective_vCPU_limit // 8 >= 1:
            return ("p3.2xlarge", self.effective_vCPU_limit // 8)
        elif self.effective_vCPU_limit >= 4:
            return ("p2.xlarge", 1)
        else:
            return ("t2.micro", 1)
        
    def create_iam_role(self):
        iam = self.session.client('iam')
        trust_policy = {
            'Version': '2012-10-17', ## Stolen from Chat GPT
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Principal': {'Service': 'ec2.amazonaws.com'},
                    'Action': 'sts:AssumeRole'
                }
            ]
        }

        permissions_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': [
                        's3:Get*',
                        's3:List*'
                    ],
                    'Resource': 'arn:aws:s3:::*'
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'sqs:*'
                    ],
                    'Resource': '*'
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'ec2:*'
                    ],
                    'Resource': '*'
                }
            ]
        }

        response = iam.create_role(
            RoleName='CloudCrack-s3-sqs-role',
            AssumeRolePolicyDocument=str(json.dumps(trust_policy))
        )

        iam.put_role_policy(
            RoleName='CloudCrack-s3-sqs-role',
            PolicyName='s3-sqs-permissions',
            PolicyDocument=str(json.dumps(permissions_policy))
        )

        return response['Role']
    
    def create_instance_profile(self): ## TODO: Ensure this works
        iam = self.session.client('iam')
        try:
            response = iam.create_instance_profile(InstanceProfileName='CloudCrack-s3-sqs-instance-profile')
            iam_role_name = self.get_iam_role()['RoleName']
            iam.add_role_to_instance_profile(InstanceProfileName='CloudCrack-s3-sqs-instance-profile', RoleName=iam_role_name)
            time.sleep(5)
            return response['InstanceProfile']['Arn']
        except ClientError as e: ##TODO: Add more specific error handling
                print(e)
                raise(e) # TODO: Fix this Anti-Pattern
           
    def get_iam_role(self):
        iam = self.session.client('iam')
        roles = iam.list_roles()
        for role in roles['Roles']:
            if role['RoleName'] == 'CloudCrack-s3-sqs-role':
                return role
        
        return self.create_iam_role()
        
    class CredentialManager:

        def __init__(self, aws_controller):
            self.aws_access_key_id = None
            self.aws_secret_access_key = None
            self.aws_controller = aws_controller

        def set_credentials(self, aws_access_key_id, aws_secret_access_key):
            with open(".env", "w") as f:
                f.write("AWS_ACCESS_KEY_ID=" + aws_access_key_id)
                f.write("\nAWS_SECRET_ACCESS_KEY=" + aws_secret_access_key)
        
        def get_credentials(self):
            if self.dotenv_present():    
                dotenv.load_dotenv()
                try:
                    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
                    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
                    return aws_access_key_id, aws_secret_access_key
                except:
                    return False
            else:
                self.run_setup()


        def get_aws_access_key_id(self):
            return self.aws_access_key_id
        
        def get_aws_secret_access_key(self):
            return self.aws_secret_access_key

        def dotenv_present(self):
            try:
                with open(".env", "r") as f:
                    dotenv = f.read()
                return True
            except:
                return False
            
        def run_setup(self):
            print("It looks like this is your first time running CloudCrack. Welcome aboard!")
            print("Lets get started by setting up your AWS credentials. You can find these instructions for this in the README.md file.")

            while True:
                aws_access_key_id = input("Enter your AWS Access Key ID: ")
                aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
                print("Please wait while I validate your credentials...")
                if self.aws_controller.test_ec2(aws_access_key_id, aws_secret_access_key):
                    print("Success! Your credentials have been validated.")
                    print("You're all set! Have fun, but remember to be safe and to only use this tool for legitimate purposes.")
                    self.set_credentials(aws_access_key_id, aws_secret_access_key)
                    return aws_access_key_id, aws_secret_access_key
                else:
                    print("Error: Failed to validate credentials. Please try again.")
                    print("If you are sure your credentials are correct, please check your internet connection and try again.")
                    print("If you are still having issues, please open an issue on GitHub.")
                    continue
                
            

