## Localstack example
Status: wip

Requirements: install localstack, pip install yaml boto3

Create a config.yaml in root directory, example:
```
# Needed localstack services
services: lambda,sqs,dynamodb,apigateway
lambdas_dir: ./lambdas
# Which localstack is for command running
which_localstack: /home/andrea/.local/bin/localstack
queues: 
- test
tables:
# tablename,HASH:type,RANGE:type
- test,uuid:S
- test1,uuid:S,prova:N
apigateway:
# method,url,lambda
- POST,test,rest
```

### Startup script
Used to configure localstack based on `config.yaml`: `python startup.py config.yaml`

### Tips
- Install module in lambda directory: `pip install module-name -t /path/to/project-dir`
- Zip lambda from command line with: `zip -r lambda.zip *`
- See apigateway rest apis: http://localhost:4567/restapis/

### Useful commands
**NOTE**: With awscli-local you can avoid to specify the endpoint
- aws --endpoint-url=http://localhost:4574 lambda create-function --function-name=f1 --runtime=python3.5 --role=r1 --handler=lambda.handler --zip-file fileb://lambda.zip
- aws --endpoint-url=http://localhost:4574 lambda delete-function --function-name=f1
- aws lambda --endpoint-url=http://localhost:4574 invoke --function-name f1 result.log --payload '{"name":"test"}'
- aws --endpoint-url=http://localhost:4574 lambda list-functions

- aws sqs create-queue --endpoint-url=http://localhost:4576 --queue-name=test
- aws sqs list-queues --endpoint-url=http://localhost:4576
- aws sqs --endpoint-url=http://localhost:4576 --queue-url=test receive-message

- aws dynamodb --endpoint-url=http://localhost:4569 create-table --table-name test --attribute-definitions AttributeName=uuid,AttributeType=S --key-schema AttributeName=uuid,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
- aws dynamodb --endpoint-url=http://localhost:4569 get-item --table-name test --key file://key.json

- aws apigateway get-resources --region us-west-2 --rest-api-id YOUR_API_ID --endpoint-url=http://localhost:4567

### Todo
- apigateway configuration not tested
