from sh import hashcat
import boto3


## Check For Two aws SQS Queues and assign them to variables
def check_infrastructure():
    sqs = boto3.resource('sqs')
    delivery = sqs.get_queue_by_name(QueueName='delivery_queue')
    control = sqs.get_queue_by_name(QueueName='control_queue')
    return delivery, control

## Check for messages in the delivery queue
def check_queue(queue):
    messages = queue.receive_messages(MaxNumberOfMessages=1)
    return messages

## Send a message to the control queue
def send_control_message(queue2, message):
    response = queue2.send_message(MessageBody=message)
    return response

def main():
    delivery, control = check_infrastructure()
    while True:
        messages = check_queue(delivery)
        if len(messages) > 0:
            for message in messages:
                print(message.body)
                message.delete()
                send_control_message(control, "Cracking...")
                hashcat(message.body)
                send_control_message(control, "Cracked!")
                break
        else:
            messages = check_queue(control)
            if len(messages) > 0:
                for message in messages:
                    print(message.body)
                    message.delete()
                    break
            else:
                continue
