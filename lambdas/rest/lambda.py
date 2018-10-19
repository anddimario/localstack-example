from cerberus import Validator
import boto3


def handler(event, context):
    print 'test'
    print event
    schema = {'name': {'type': 'string'}}
    v = Validator()
    validation = v.validate(event, schema)
    if not validation:
        print('invalid')
        raise Exception('Validation error')
    client = boto3.client('sqs', endpoint_url='http://localhost:4576')
    response = client.send_message(
        QueueUrl='http://localhost:4576/queue/test',
        MessageBody=event['name']
    )
    print(response)
    return {'foo': 'bar'}
