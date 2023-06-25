from job_handler import JobHandler, STATUS
import boto3
from botocore.exceptions import ClientError
from errors import MaskFormatError
import json
import dotenv
import os
import time
import uuid
import signal

## Problems:
## TODO: Finish settings menu and add a way to change settings and save them to the config fil
## TODO: Potentially add a seperate control queue for each Ec2 hashing instance

class ClientController:

    def __init__(self):
        self.config = self.get_config()
        if not self.config["offline_mode"]:
            self.aws_controller = AwsController(self.config, "client")
            self.job_handler = JobHandler(self.aws_controller, "client", self.config["debug_mode"])
        
    def run(self):
        self.print_welcome()
        signal.signal(signal.SIGINT, self.handle_interrupt)
        while True:
            user_input = input("\nCloudCrack > ")
            if not self.config["offline_mode"]:
                self.job_handler.check_for_response()
            user_input.strip()
            input_as_list = user_input.split(" ")

            if input_as_list[0] == "help":
                self.print_help()
            elif input_as_list[0] in ["exit", "close", "quit"]:
                if not self.config["offline_mode"]:
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
            elif input_as_list[0] ==  "settings":
                self.options_screen()
            else:
                print("Unknown Command -- Type 'help' for a list of commands")

    def handle_interrupt(self, signal, frame):
        print("\nExiting...")
        try:
            self.aws_controller.cleanup()
        except:
            pass
        exit(0)

    def print_welcome(self):
        print(""" 
             _______  ___      _______  __   __  ______   _______  ______    _______  _______  ___   _ 
            |       ||   |    |       ||  | |  ||      | |       ||    _ |  |   _   ||       ||   | | |
            |       ||   |    |   _   ||  | |  ||  _    ||       ||   | ||  |  |_|  ||       ||   |_| |
            |       ||   |    |  | |  ||  |_|  || | |   ||       ||   |_||_ |       ||       ||      _|
            |      _||   |___ |  |_|  ||       || |_|   ||      _||    __  ||       ||      _||     |_ 
            |     |_ |       ||       ||       ||       ||     |_ |   |  | ||   _   ||     |_ |    _  |
            |_______||_______||_______||_______||______| |_______||___|  |_||__| |__||_______||___| |_|

            """)
        print("Welcome to Cloud Crack v1.1")
        print("Type 'help' for a list of commands")

    def print_help(self):
        print("\nhelp - print this message")
        print("exit - exit CloudCrack")
        print("show <all> / <job_id>) - list all jobs or show a specific job")
        print("create - create a new job")
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
                print("Progress: " + str(round(job.progress[0] / job.progress[1], 4) * 100) + "%")
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

            if input_as_list[0].lower() == "options":
                print("Options:")
                print("Hash: " + _hash)
                print("Hash Type: " + hash_type)
                print("Attack Mode: " + str(attack_mode))
                print("Mask: " + mask)
                print("Dictionary: " + dictionary)
                print("Output (Optional - Location of desired text file for output): " + output_file)
                print("Hashes (Optional - Location of bulk hash file): " + hash_file_location)
            elif input_as_list[0].lower() == "help":
                print("\nhelp - print this message")
                print("exit - return to the main menu")
                print("set <option> <value> - set an option to a value")
                print("run - run the job")
                print("options - list the current options and their values")
                print("clear - clear all options")

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
                    if not self.is_valid_mask(mask):
                        mask = ""
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
                if attack_mode == 3 and not self.is_valid_mask(mask): ## TODO: Remove this if unnecessary
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

                if output_file != "":
                    if self.config["debug_mode"] == True:
                        print("[DEBUG] Attempting to Locate Output File: " + output_file)
                    try:
                        with open(output_file, "w") as file:
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Successfully Located Output File")
                    except:
                        with open(output_file, "x") as file:
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Successfully Created Output File")
                
                if hash_file_location != "":
                    if self.config["debug_mode"] == True:
                        print("[DEBUG] Attempting to Get Hash file location: " + hash_file_location)
                    try:
                        with open(hash_file_location, "r") as file:
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Successfully Located Hash File")
                    except:
                        print("Failed to open hash file. Please check the file location and try again")
                        continue

                    with open(hash_file_location, "r") as file:
                        hashes = file.readlines()
                    for _hash in hashes:
                        _hash = _hash.strip(" ")
                        _hash = _hash.strip("\n")
                        try: 
                            jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info, output_file)
                            self.job_handler.send_job(jb)
                        except Exception as e:
                            print(f"Failed To Create Job For Hash: {_hash}")
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Failed To Create Job For Hash: " + _hash)
                                print(f"[DEBUG] Reason: {e}")
                            continue
                else:
                    jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info, output_file)
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
    
    def options_screen(self):
        user_input = ""
        
        while user_input != "back" and user_input != "exit":
            self.show_current_settings()
            user_input = input("\nCloudCrack > Settings > ")
            input_as_list = user_input.split(" ")
            if input_as_list[0] == "set":
                if input_as_list[1] in self.config:
                    if self.set_option(input_as_list[1], input_as_list[2]):
                        print(f"Successfully set {input_as_list[1]} to {input_as_list[2]}")
                    else:
                        print(f"Failed to set {input_as_list[1]} to {input_as_list[2]}")
                else:
                    print(f"Invalid option {input_as_list[1]}")


                    
    def set_option(self, option, value):
        if value == None or value == "":
            return False
        try:
            with open("config.json", "r") as file:
                config = json.load(file)
                config[option] = value
            with open("config.json", "w") as file:
                json.dump(config, file)
                self.config = config
            return True
        except:
            print("Failed to open config file")
            return False
        

    def show_current_settings(self):
        print("\nCurrent Settings:")
        option_categories = []
        for option in self.config:
            option_categories.append(option)
            print(f"{option}: {self.config[option]}")

        return option_categories
    
    def is_valid_mask(self, mask):
        valid_keyspaces = ["l", "u", "d", "h", "H", "s", "a", "b"]
        try:
            if mask == None or mask == "":
                raise MaskFormatError("Mask cannot be None or empty")
            
            if "?" not in mask:
                raise MaskFormatError("Mask must contain at least one ? character")
            
            if len(mask) <= 1:
                raise MaskFormatError("Mask must have at least two characters")
            
            for i in range(len(mask)):
                char = mask[i]
                if char == " ":
                    raise MaskFormatError("Mask cannot contain spaces")
                if char == "?":
                    if i < len(mask) - 1 and mask[i + 1] not in valid_keyspaces:
                        raise MaskFormatError("Invalid keyspace")
            return True
        except MaskFormatError as e:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Mask Format Error: " + str(e))
            else:
                print("Invalid Mask: " + str(e))
            return False
         
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
        print("To use CloudCrack, you need to increase this limit to at least 4. (>= 8 recommended)")
        print("You can apply for a limit increase here: https://console.aws.amazon.com/servicequotas/home?region=us-east-2#!/services/ec2/quotas/L-417A185B")



class AwsController:
    def __init__(self, config, mode):
            self.config = config
            if mode == "client":
                self.credentialManager = self.CredentialManager(self, self.config)
            self.session = None
            self.instances = []
            self.instance_profile = None
            
            if mode == "client":
                if self.test_ec2(self.credentialManager.get_aws_access_key_id(), self.credentialManager.get_aws_secret_access_key()):
                    self.session = self.get_session("client")
                else:
                    exit()
                if not self.test_sqs() and not self.test_s3():
                    exit()
                
                self.effective_vCPU_limit = self.get_vCPU_limit() * int(self.config["usage_limit"])
                self.instance_config = self.get_recomended_instance_config()
            elif mode == "server":
                self.session = self.get_session("server")


    
    def test_ec2(self, aws_access_key_id, aws_secret_access_key):
        try:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Testing EC2 Permissions")
            client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
            client.run_instances(ImageId=self.config['AWS-Settings']["image_id"], MinCount=1, MaxCount=1, InstanceType='t2.micro', DryRun=True)
            return True  
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error: {e.response['Error']['Code']}")
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: EC2 Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
            elif 'DryRunOperation' not in str(e):
                print("Error: Your credentials are invalid. Please make sure you entered them correctly.\n")
                return False
            elif 'DryRunOperation' in str(e):
                return True

        
    def test_s3(self):
        try:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Testing S3 Permissions")
            s3 = self.session.client('s3')
            s3.list_buckets(DryRun=True)
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error: {e.response['Error']['Code']}")
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: S3 Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
            elif 'DryRunOperation' in str(e):
                    return True
            else:
                return False
    
    def test_sqs(self):
        try:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Testing SQS Permissions")
            sqs = self.session.resource('sqs')
            queue = sqs.create_queue(QueueName="test.fifo", Attributes={'DelaySeconds': '1', 
                                                            'FifoQueue': 'true', 
                                                            'ContentBasedDeduplication': 'true'})
            queue.delete()
            return True
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error: {e.response['Error']['Code']}")
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: SQS Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
        return False
        
    def get_session(self, mode):
        if mode == "client":
            dotenv.load_dotenv()
            if self.config["debug_mode"] == True:
                print("[DEBUG] Loading AWS Credentials from .env file")
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            session = boto3.Session(aws_access_key_id=aws_access_key_id, 
                                    aws_secret_access_key=aws_secret_access_key, 
                                    region_name='us-east-2')
            if self.config["debug_mode"] == True:
                print("[DEBUG] Succesfully Established AWS Session")
        else:
            session = boto3.Session(region_name='us-east-2')
        return session
    
    def get_vCPU_limit(self):
        quota_client = self.session.client('service-quotas')
        response = quota_client.get_service_quota(ServiceCode='ec2', QuotaCode='L-417A185B')
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] vCPU Limit: {response['Quota']['Value']}")
        return int(response['Quota']['Value'])
    
    def get_instances(self):
        return self.instances
    
    def create_queue(self, queue_name):
        sqs = self.session.resource('sqs')
        try:
            queue = sqs.create_queue(QueueName=queue_name + ".fifo", Attributes={'DelaySeconds': '1', 
                                                            'FifoQueue': 'true', 
                                                            'ContentBasedDeduplication': 'true'})
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Created Queue: {queue_name}")
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error: {e.response['Error']['Code']}")
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
            self.cleanup()
            exit()
        return queue
    
    def message_queue(self, queue, message_body, message_type): ## TODO: FINISH ERROR HANDLING
        try:
            response = queue.send_message(MessageBody=message_body, MessageGroupId=message_type)
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Sent {message_type} to {queue}")
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
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Locating Queue: {name}")
        sqs = self.session.resource('sqs')
        try:
            queue = sqs.get_queue_by_name(QueueName=name + ".fifo")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                return
        return queue
    
    def create_instance(self):
        ec2 = self.session.resource('ec2')
        if self.instance_profile is None:
            self.instance_profile = self.create_instance_profile()
        try:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Creating New Instance..")
            instance = ec2.create_instances(ImageId=self.config["image_id"], 
                                            MinCount=1, 
                                            MaxCount=1, 
                                            InstanceType=self.instance_config[0], IamInstanceProfile={'Arn': self.instance_profile})
            self.instances.append(instance[0])
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error When Creating Instance: {e.response['Error']['Code']}")
            if e.response['Error']['Code'] == 'InsufficientInstanceCapacity':
                print("Error: Failed to create instances. Looks like those pesky ML engineers are using all the GPU instances.")
                if len(instance) == 0:
                    print("Please try again later or try a different region. (Specify this in config.json file)")
                else:
                    print(f"Only Secured {self.get_num_instances()}. You can continue with this number of instances, but you will experience decreased performance.")
                    print("You can also try again later or try a different region. (Specify this in the settings menu)")
            elif e.response['Error']['Code'] == 'VcpuLimitExceeded':
                print("VCPU Limit Exceeded - Likely due to Known Issue #1")
                return
            else:
                print(e)
        except Exception as e:
            print(e)

    
    def create_bucket(self, bucket_prefix):
        s3 = self.session.client('s3')
        bucket_name = self.create_bucket_name(bucket_prefix)
        try:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Creating Bucket: {bucket_name}")
            bucket = s3.create_bucket(Bucket=bucket_name, 
                                      CreateBucketConfiguration={'LocationConstraint': "us-east-2"})
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error When Creating Bucket: {e.response['Error']['Code']}")
            print("Error: Failed to create bucket. Please check your AWS Permissions and try again.") ## TODO: NEED MORE SPECIFIC ERROR HANDLING
            return False ## TODO: Raise exception instead of returning False
        return bucket_name
    
    def upload_file(self, file_path, bucket_name, file_name):
        try:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Uploading File: {file_name}")
            self.session.client('s3').upload_file(file_path, bucket_name, file_name)
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error When Uploading File: {e.response['Error']['Code']}")
            else:
                print("Error: Failed to upload file. Please check your AWS Permissions and try again.")
            return False
        return True
    
    def download_file(self, bucket_name, file_name, local_name):
        try:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Downloading File: {file_name}")
            self.session.client('s3').download_file(bucket_name, file_name, local_name)
            return local_name
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error When Downloading File: {e.response['Error']['Code']}")
            else:
                print("Error: Failed to download file. Please check your AWS credentials and try again.")
    
    def create_bucket_name(self, bucket_prefix):
        return ''.join([bucket_prefix, str(uuid.uuid4())])
    
    def close_instances(self):
        ec2 = self.session.resource('ec2')
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Closing All Instances..")
        for instance in self.instances:
            instance.terminate()

    def close_buckets(self):
        s3 = self.session.resource('s3')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Closing All Buckets..")

        buckets = s3.buckets.all()
        for bucket in buckets:
            bucket.objects.all().delete()
            bucket.delete()
    
    def close_queues(self):
        sqs = self.session.resource('sqs')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Closing All Queues..")
            
        queues = sqs.queues.all()
        for queue in queues:
            queue.delete()

    def remove_iam_role(self):
        iam = self.session.client('iam')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Removing IAM Role..")

        roles = iam.list_roles()
        for role in roles['Roles']:
            if role['RoleName'] == 'CloudCrack-s3-sqs-role':
                iam.delete_role_policy(RoleName='CloudCrack-s3-sqs-role', PolicyName='s3-sqs-permissions')
                iam.delete_role(RoleName='CloudCrack-s3-sqs-role')
                return True
        return False
    
    def remove_instance(self, instance_id):
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Removing Instance From Local List: {instance_id}")
        for instance in self.instances:
            if instance.id == instance_id:
                self.instances.remove(instance)
                print("Idle Instance Terminated")
                break
            
    def remove_instance_profile(self):
        iam = self.session.client('iam')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Removing Instance Profile..")

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
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Cleanup Started..")

        self.close_instances()
        self.close_buckets()
        self.close_queues()
        self.remove_instance_profile()
        self.remove_iam_role()

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Cleanup Finished")

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

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Creating IAM Role..")

        trust_policy = {
            'Version': '2012-10-17',
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

        try:
            response = iam.create_role(
                RoleName='CloudCrack-s3-sqs-role',
                AssumeRolePolicyDocument=str(json.dumps(trust_policy))
            )

            iam.put_role_policy(
                RoleName='CloudCrack-s3-sqs-role',
                PolicyName='s3-sqs-permissions',
                PolicyDocument=str(json.dumps(permissions_policy))
            )
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error When Creating IAM Role {e.response['Error']['Code']}")

            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: IAM Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False
            elif e.response['Error']['Code'] == 'EntityAlreadyExists':
                pass
            else:
                return False

        return response['Role']
    
    def create_instance_profile(self): ## TODO: Ensure this works
        iam = self.session.client('iam')
        try:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Creating Instance Profile..")
            response = iam.create_instance_profile(InstanceProfileName='CloudCrack-s3-sqs-instance-profile')
            iam_role_name = self.get_iam_role()['RoleName']
            iam.add_role_to_instance_profile(InstanceProfileName='CloudCrack-s3-sqs-instance-profile', RoleName=iam_role_name)
            time.sleep(5)
            return response['InstanceProfile']['Arn']
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error When Creating Instance Profile {e.response['Error']['Code']}")
                raise(e)
           
    def get_iam_role(self):
        iam = self.session.client('iam')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Getting IAM Role..")

        roles = iam.list_roles()
        for role in roles['Roles']:
            if role['RoleName'] == 'CloudCrack-s3-sqs-role':
                return role
        
        return self.create_iam_role()
        
    class CredentialManager:

        def __init__(self, aws_controller, config):
            self.config = config
            self.aws_controller = aws_controller
            self.aws_access_key_id, self.aws_secret_access_key = self.get_credentials()

        def set_credentials(self, aws_access_key_id, aws_secret_access_key):
            with open(".env", "w") as f:
                f.write("AWS_ACCESS_KEY_ID=" + aws_access_key_id)
                f.write("\nAWS_SECRET_ACCESS_KEY=" + aws_secret_access_key)
        
        def get_credentials(self):
            if self.dotenv_present():
                dotenv.load_dotenv()
                try:
                    if self.config["debug_mode"] == True:
                        print(f"[DEBUG] Fetching AWS Credentials from .env file..")
                    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
                    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
                    return aws_access_key_id, aws_secret_access_key
                except:
                    raise Exception("Error: Failed to load AWS credentials from .env file. Please check the file and try again.")
            else:
                self.run_setup()
                return self.get_credentials()

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
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Running Setup..")

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
                
            
