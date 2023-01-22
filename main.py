import boto3;



# Create an ec2 resource
ec2 = boto3.resource('ec2')

for instance in ec2.instances.all():
    print(instance.id, instance.state)