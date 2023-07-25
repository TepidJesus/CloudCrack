from botocore.exceptions import ClientError
from errors import CredentialsFileNotFoundError, EnvironmentVariableNotFoundError, AWSPermissionsError, AWSCredentialError
import boto3
import dotenv
import os
import time
import uuid
import json

class AwsController: 
    def __init__(self, config, mode): # Should throw an error if the config is invalid
            self.config = config
            if mode == "client":
                try:
                    self.credentialManager = self._CredentialManager(self, self.config)
                except :
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
                if self.effective_vCPU_limit < 4:
                    self.vcpu_limit_message(self.effective_vCPU_limit)
                    
                self.instance_config = self.get_recomended_instance_config()
            elif mode == "server":
                self.session = self.get_session("server")

    def vcpu_limit_message(self, limit):
        print("It looks like your AWS account has a P-Instance vCPU limit of " + str(limit) + ".")
        print("To use CloudCrack, you need to increase this limit to at least 4. (>= 8 recommended)")
        print("You can apply for a limit increase here: https://console.aws.amazon.com/servicequotas/home?region=us-east-2#!/services/ec2/quotas/L-417A185B")


    def test_ec2(self, aws_access_key_id, aws_secret_access_key):
        try:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Testing EC2 Permissions")
            client = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
            client.run_instances(ImageId=self.config["image_id"], MinCount=1, MaxCount=1, InstanceType='t2.micro', DryRun=True)
            return True  # Should return nothing if successful
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error: {e.response['Error']['Code']}")

            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: EC2 Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                raise AWSPermissionsError("EC2 Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
            elif 'DryRunOperation' not in str(e):
                print("Error: Your credentials are invalid. Please make sure you entered them correctly.\n")
                raise AWSCredentialError("Invlaid Credentials")
            return

        
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
                return False #NEWERRORNEEDED
            elif 'DryRunOperation' in str(e):
                    return True # Should return nothing if successful
            else:
                return False #NEWERRORNEEDED
    
    def test_sqs(self):
        try:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Testing SQS Permissions")
            sqs = self.session.resource('sqs')
            queue = sqs.create_queue(QueueName="test.fifo", Attributes={'DelaySeconds': '1', 
                                                            'FifoQueue': 'true', 
                                                            'ContentBasedDeduplication': 'true'})
            queue.delete()
            return True # Should return nothing if successful
        except ClientError as e:
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Error: {e.response['Error']['Code']}")
            if e.response['Error']['Code'] == 'AccessDenied':
                print("Error: SQS Permission Test FAILED. Please make sure you have the correct permissions enabled for your IAM user.")
                print("You can find the required permissions in the setup guide in the README.md file.")
                return False #NEWERRORNEEDED
        return False #NEWERRORNEEDED
        
    def get_session(self, mode): # TODO: Should throw custom error if the sessopm cannot be established
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
    
    def get_vCPU_limit(self): # TODO: Should throw custom error if the limit cannot be found
        quota_client = self.session.client('service-quotas')
        response = quota_client.get_service_quota(ServiceCode='ec2', QuotaCode='L-417A185B')
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] vCPU Limit: {response['Quota']['Value']}")
        return int(response['Quota']['Value'])
    
    def get_instances(self):
        return self.instances
    
    def create_queue(self, queue_name): # TODO: Should throw custom error if the queue cannot be created
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
                exit() #NEWERRORNEEDED
            elif e.response['Error']['Code'] == 'AWS.SimpleQueueService.QueueNameExists':
                print(f"Error: Looks like you already have a queue with the name {queue_name}. If you made this queue yourself, please delete or rename it and try again.")
                exit() #NEWERRORNEEDED
            else:
                print(e) # Handle don't show
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
                        return False #NEWERRORNEEDED
            if message_type == "Job":
                print(f"Error: Failed to send Job {message_body['job_id']} to the queue.")
            else:
                print(f"Error: Failed to send {message_type} to the queue.")
            return False #NEWERRORNEEDED
        
    def locate_queue(self, name):
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Locating Queue: {name}")
        sqs = self.session.resource('sqs')
        try:
            queue = sqs.get_queue_by_name(QueueName=name + ".fifo")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                return #NEWERRORNEEDED
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
            print(e) # Should handle don't show

    
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
            return False # Raise exception instead of returning False
        return True # Remove
    
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
            return False # Raise exception instead of returning False
    
    def create_bucket_name(self, bucket_prefix):
        return ''.join([bucket_prefix, str(uuid.uuid4())]) # Should handle exception if one occurs
    
    def close_instances(self): # Needs error handling
        ec2 = self.session.resource('ec2')
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Closing All Instances..")
        for instance in self.instances:
            instance.terminate()

    def close_buckets(self):  # Needs error handling
        s3 = self.session.resource('s3')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Closing All Buckets..")

        buckets = s3.buckets.all()
        for bucket in buckets:
            bucket.objects.all().delete()
            bucket.delete()
    
    def close_queues(self):  # Needs error handling
        sqs = self.session.resource('sqs')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Closing All Queues..")
            
        queues = sqs.queues.all()
        for queue in queues:
            queue.delete()

    def remove_iam_role(self):  # Needs error handling
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
    
    def remove_instance(self, instance_id):  # Needs error handling
        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Removing Instance From Local List: {instance_id}")
        for instance in self.instances:
            if instance.id == instance_id:
                self.instances.remove(instance)
                print("Idle Instance Terminated")
                break
            
    def remove_instance_profile(self):  # Needs error handling
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
                return True # Remove
        return False # Raise exception instead of returning False

    def cleanup(self):  # Handle errors from all cleanup functions
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
        return self.instance_config[1]  # Needs error handling

    def get_recomended_instance_config(self):  # Needs error handling
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
                return False # Raise exception instead of returning False
            elif e.response['Error']['Code'] == 'EntityAlreadyExists':
                pass
            else:
                return False # Raise exception instead of returning False

        return response['Role']
    
    def create_instance_profile(self):
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
           
    def get_iam_role(self):  # Needs error handling
        iam = self.session.client('iam')

        if self.config["debug_mode"] == True:
            print(f"[DEBUG] Getting IAM Role..")

        roles = iam.list_roles()
        for role in roles['Roles']:
            if role['RoleName'] == 'CloudCrack-s3-sqs-role':
                return role
        
        return self.create_iam_role()
    
    class _CredentialManager:

        def __init__(self, aws_controller, config):
            self.config = config
            self.aws_controller = aws_controller
            try:
                self.aws_access_key_id, self.aws_secret_access_key = self.get_credentials()
            except CredentialsFileNotFoundError or EnvironmentVariableNotFoundError:
                self.aws_access_key_id, self.aws_secret_access_key = self.run_setup()
            except Exception as e:
                raise(e)

        def set_credentials(self, aws_access_key_id, aws_secret_access_key):  # Needs error handling
            with open(".env", "w") as f:
                f.write("AWS_ACCESS_KEY_ID=" + aws_access_key_id)
                f.write("\nAWS_SECRET_ACCESS_KEY=" + aws_secret_access_key)
        
        def get_credentials(self):  # Needs error handling
            if dotenv.load_dotenv():
                if self.config["debug_mode"] == True:
                    print(f"[DEBUG] Fetching AWS Credentials from .env file..")
                aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
                aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

                if aws_access_key_id == None or aws_secret_access_key == None:
                    raise EnvironmentVariableNotFoundError("AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not found in .env file.\nPlease delete the .env file and run CC again.")
                
                return aws_access_key_id, aws_secret_access_key
                 
            else:
                raise CredentialsFileNotFoundError("Dotenv file not found.")

        def get_aws_access_key_id(self):
            return self.aws_access_key_id
        
        def get_aws_secret_access_key(self):
            return self.aws_secret_access_key

        def run_setup(self):
            if self.config["debug_mode"] == True:
                print(f"[DEBUG] Running Setup..")

            print("It looks like this is your first time running CloudCrack. Welcome aboard!")
            print("Lets get started by setting up your AWS credentials. You can find these instructions for this in the README.md file.")

            while True:
                aws_access_key_id = input("Enter your AWS Access Key ID: ")
                aws_secret_access_key = input("Enter your AWS Secret Access Key: ")
                print("Please wait while I validate your credentials...")
                try:
                    self.aws_controller.test_ec2(aws_access_key_id, aws_secret_access_key)
                    print("Success! Your credentials have been validated.")
                    print("You're all set! Have fun, but remember to be safe and to only use this tool for legitimate purposes.")
                    self.set_credentials(aws_access_key_id, aws_secret_access_key)
                    return aws_access_key_id, aws_secret_access_key
                except:
                    print("Error: Failed to validate credentials. Please try again.")
                    print("If you are sure your credentials are correct, please check your internet connection and try again.")
                    print("If you are still having issues, please open an issue on GitHub.")
                    continue