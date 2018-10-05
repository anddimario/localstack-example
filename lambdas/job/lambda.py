import boto3
import uuid

def handler(event, context):
    print 'test'
    sqs = boto3.client('sqs', endpoint_url='http://localhost:4576')
    sqs_response = sqs.receive_message(
        QueueUrl='123456789012/test',
    )
    dynamo = boto3.client('dynamodb', endpoint_url='http://localhost:4569')
    print(sqs_response['Messages'][0])
    item_uuid = str(uuid.uuid4())
    print item_uuid
    dynamo_response = dynamo.put_item(
        TableName='test',
        Item={
            'uuid': {
                'S': item_uuid
            },
            'value': {
                'S': sqs_response['Messages'][0]['Body']
            }
        }
    )
    return {'foo': 'bar'}

