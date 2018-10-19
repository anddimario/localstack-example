#!/usr/bin/python

import os
import signal
import sys
import zipfile
import subprocess
import psutil
import time
import yaml
import boto3

def start_localstack():
    print('start localstack')
    # start localstack
    os.environ['SERVICES'] = services
    subprocess.Popen([yaml_params['which_localstack'], 'start'],
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)

def kill_running(name):
    for proc in psutil.process_iter():
        if proc.name() == name:
            print('kill already started localstack')
            os.kill(proc.pid, signal.SIGTERM)
    time.sleep(10)

def get_yaml(config_path):
    # read the config
    # https://www.guru99.com/reading-and-writing-files-in-python.html#3
    f = open(config_path, "r")
    contents = ""
    if f.mode == 'r':
        contents = f.read()
    # decode yaml
    # https://pyyaml.org/wiki/PyYAMLDocumentation?version=2
    params = yaml.load(contents)
    return params

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def create_lambda(lambda_dir):
    client = boto3.client('lambda', endpoint_url='http://localhost:4574', region_name='us-west-2')
    # send lambda
    with open("lambda.zip", "rb") as f:
        bytes = f.read()
        # clean the zip
        os.remove("lambda.zip")
        client.create_function(
            Code={
                'ZipFile': bytes
            },
            FunctionName=lambda_dir,
            Runtime='python3.6',
            Role='r1',
            Handler='lambda.handler',
        )

def configure_lambdas(lambdas_dir):
    print("configure lambdas")
    main_path = os.getcwd()
    # in config there's the basic lambdas dir
    lambdas_dirs = os.listdir(lambdas_dir)
    for lambda_dir in lambdas_dirs:
        # create zip
        lambda_path = '/' + lambdas_dir + '/' + lambda_dir
        os.chdir(os.getcwd() + lambda_path)
        zipf = zipfile.ZipFile('lambda.zip', 'w', zipfile.ZIP_DEFLATED)
        zipdir('.', zipf)
        zipf.close()
        create_lambda(lambda_dir)
        # return to old path
        os.chdir(main_path)
        print('added lambda ' + lambda_dir)

def configure_sqs(queues):
    print("configure queues")
    client = boto3.client('sqs', endpoint_url='http://localhost:4576')
    for queue in queues:
        response = client.create_queue(
            QueueName=queue,
        )
        print('added queue ' + queue)

def configure_dynamo(tables):
    print("configure tables")
    client = boto3.client('dynamodb', endpoint_url='http://localhost:4569')
    for table in tables:
        info = table.split(',')
        tablename = info.pop(0)
        hashkey = info[0].split(':')
        AttributeDefinitions = [
            {
                'AttributeName': hashkey[0],
                'AttributeType': hashkey[1]
            },
        ]
        KeySchema=[
            {
                'AttributeName': hashkey[0],
                'KeyType': 'HASH'
            },
        ]
        if len(info) == 2:
            rangekey = info[1].split(':')
            AttributeDefinitions.append({
                'AttributeName': rangekey[0],
                'AttributeType': rangekey[1]
            })
            KeySchema.append({
                'AttributeName': rangekey[0],
                'KeyType': 'RANGE'
            })
        response = client.create_table(
            AttributeDefinitions=AttributeDefinitions,
            TableName=tablename,
            KeySchema=KeySchema,
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
        print('added table ' + table)

def configure_apigateway(apis):
    # https://ig.nore.me/2016/03/setting-up-lambda-and-a-gateway-through-the-cli/
    # https://gist.github.com/crypticmind/c75db15fd774fe8f53282c3ccbe3d7ad
    print("configure apigateway")
    client = boto3.client('apigateway', endpoint_url='http://localhost:4567', region_name='us-west-2')
    response_create_rest_api = client.create_rest_api(
        name='test',
    )
    response_get_rest_apis = client.get_rest_apis()
    rest_api_id = response_get_rest_apis['items'][0]['id']
    response_get_resources = client.get_resources(
        restApiId=rest_api_id,
    )
    parent_resource_id = response_get_resources['items'][0]['id']
    for api in apis:
        info = api.split(',')
        response_create_resource = client.create_resource(
            restApiId=rest_api_id,
            parentId=parent_resource_id,
            pathPart=info[1]
        )
        response_get_resources = client.get_resources(
            restApiId=rest_api_id,
        )
        resource_id = response_get_resources['items'][0]['id']
        client.put_method(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=info[0],
            authorizationType='NONE',
        )
        client.put_integration(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=info[0],
            type='AWS_PROXY',
            integrationHttpMethod=info[0],
            uri='arn:aws:apigateway:us-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:us-west-2:000000000000:function:' + info[2] + '/invocations',
        )
        client.put_method_response(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=info[0],
            statusCode='200',
        )
        client.put_integration_response(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=info[0],
            statusCode='200',
            selectionPattern='.*',
        )
    client.create_deployment(
        restApiId=rest_api_id,
        stageName='test'
    )
    print('apigateway endpoint: ' + 'POST' + ' http://localhost:4567/restapis/' + rest_api_id + '/test/_user_request_/' + info[1])
    # see apis on http://localhost:4567/restapis/

# read from argv where config is
yaml_params = get_yaml(sys.argv[1])
services = yaml_params['services']

kill_running('localstack')
start_localstack()
# wait before configure sources
time.sleep(10)

# lambdas
if 'lambda' in services:
    configure_lambdas(yaml_params['lambdas_dir'])

# sqs
if 'sqs' in services:
    configure_sqs(yaml_params['queues'])

# dynamo
if 'dynamo' in services:
    configure_dynamo(yaml_params['tables'])

# api gateway
if 'apigateway' in services:
    configure_apigateway(yaml_params['apigateway'])
