# Swagger

This README documents the commands used to create the swagger docs for the API catalogue and the model files for use in APIGEE.

If you need to manually generate the swagger after making a change then the following commands in this order will create the correct results:

## Command order

```shell
nrlf swagger generate
nrlf swagger merge producer
nrlf swagger merge consumer
```

## Generate

The generate command recreates the two swagger files for the consumer and producer using the fhir swagger generator - it will then use that `./api/*/swagger.yaml` file to generate the pydantic models using the datamodel-codegen package


## Merge

The merge command will take the changes in the static swagger files and merge them into the freshly generated swagger.yaml files, it will do the following:
- remove commented lines
- replace the snake case terms
- remove some auto generated fields we dont need

It will then:
- merge in the narrative and other changes from the static files into the `/api/*/swagger.yaml`

And finally:
- remove all information that is not required for public documentation (e.g. security sections and authorisers) and put that into the `nrl-*-api.yaml` files
