import boto3;



# Create an ec2 resource
ec2 = boto3.resource('ec2')
AMI_ID = 'ami-0d'
# Create a new P4 Large EC2 instance with the AMI ID
instances = ec2.create_instances(
    ImageId=AMI_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType='p4d.24xlarge',
    ) 