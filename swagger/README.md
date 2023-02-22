# Swagger

This README documents the commands used to create the swagger docs for the API catalogue and the model files for use in APIGEE.

## 1. Generate Swagger docs for the API catalogue
The Swagger docs generated in this step merge the docs in ./swagger.<br />
To generate ./api/consumer/nrl-consumer-api.yaml for the API catalogue and ./api/consumer/swagger.yaml for the consumer model file:
```shell
nrlf swagger merge consumer
```
To generate ./api/producer/nrl-producer-api.yaml for the API catalogue and ./api/producer/swagger.yaml for the producer model file:
```shell
nrlf swagger merge producer
```

## 2. Generate the model files from the Swagger docs
To generate the model files layer/nrlf/nrlf/consumer/fhir/r4/model.py and layer/nrlf/nrlf/producer/fhir/r4/model.py for APIGEE from the swagger.yaml docs created in step 1.
```shell
nrlf swagger generate-model
```