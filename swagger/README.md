# Swagger

This README documents the commands used to create the swagger docs for the API catalogue and the model files for use in APIGEE.

If you need to manually generate the swagger after making a change then the following commands in this order will create the correct results:

```shell
make swagger-merge TYPE={type}
```

With TYPE being one of the following: `consumer` or `producer`.

This command uses the merge command from the swagger.sh script which will take the changes in the static swagger files and merge them into the freshly generated swagger.yaml files, it will do the following:

- remove commented lines
- replace the snake case terms
- remove some auto generated fields we dont need

It will then:

- merge in the narrative and other changes from the static files into the `/api/*/swagger.yaml`

And finally:

- remove all information that is not required for public documentation (e.g. security sections and authorisers) and put that into the `nrl-*-api.yaml` files

## Generate Model - DO NOT DO THIS UNLESS NEW PYDANTIC MODELS ARE REQUIRED

PLEASE DO NOT USE THIS COMMAND UNLESS EXPLICITLY TOLD TO DO SO. This command is only useful when we need to generate the new Pydantic Models, but FHIR does not update often enough to warrant regenerating the models constantly.

The generate- command will use that `./api/*/swagger.yaml` file that was generated in the swagger-merge step, to generate the pydantic models using the datamodel-codegen package

you can run the model generate using the below command:

```shell
make generate-model TYPE={type}
```

With TYPE being one of the following: `consumer` or `producer`.

## Generate - DO NOT DO THIS UNLESS EXPLICITLY TOLD TO

PLEASE DO NOT USE THIS COMMAND UNLESS EXPLICITLY TOLD TO DO SO. This command was useful when NRLF was in it's infancy, but since then the generated swagger files have been manually modified, so running this command will lose ALL of that that information! instead please use generate-model steps as mentioned above.

The generate command recreates the two swagger files for the consumer and producer using the fhir swagger generator - it will then use that `./api/*/swagger.yaml` file to generate the pydantic models using the datamodel-codegen package

you can run the swagger generate using the below command:

```shell
 ./scripts/swagger.sh generate
```
