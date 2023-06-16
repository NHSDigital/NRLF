# Swagger

This README documents the commands used to create the swagger docs for the API catalogue and the model files for use in APIGEE.

If you need to manually generate the swagger after making a change then the following commands in this order will create the correct results:

## Command order

```shell
nrlf swagger merge producer
nrlf swagger merge consumer
nrlf swagger generate-model producer
nrlf swagger generate-model consumer
```

## Generate - DO NOT DO THIS UNLESS EXPLICITLY TOLD TO

PLEASE DO NOT USE THIS COMMAND UNLESS EXPLICITLY TOLD TO DO SO. This command was useful when NRLF was in it's infancy, but since then the generated swagger files have been manually modified, so running this command will lose ALL of that that information! instead please use generate-model steps as mentioned above.

The generate command recreates the two swagger files for the consumer and producer using the fhir swagger generator - it will then use that `./api/*/swagger.yaml` file to generate the pydantic models using the datamodel-codegen package

you can run the swagger generate using the below command:

```shell
nrlf swagger generate
```

## Merge

The merge command will take the changes in the static swagger files and merge them into the freshly generated swagger.yaml files, it will do the following:

- remove commented lines
- replace the snake case terms
- remove some auto generated fields we dont need

It will then:

- merge in the narrative and other changes from the static files into the `/api/*/swagger.yaml`

And finally:

- remove all information that is not required for public documentation (e.g. security sections and authorisers) and put that into the `nrl-*-api.yaml` files
