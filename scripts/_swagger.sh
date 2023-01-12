#!/bin/bash

function _swagger_help() {
    echo
    echo "nrlf swagger <command> [options]"
    echo
    echo "commands:"
    echo "  help                         - this help screen"
    echo "  generate <options>           - generate all swagger and models or producer/consumer if specified"
    echo "  generate-swagger <options>   - generate all swagger or producer/consumer if specified"
    echo "  generate-model <options>     - generate all models or producer/consumer if specified"
    echo "  merge <options>              - generates the nrl-<type>-api.yml file"
}

function _get_generator() {
    mkdir ./tools
    curl https://repo1.maven.org/maven2/com/ibm/fhir/fhir-swagger-generator/4.11.1/fhir-swagger-generator-4.11.1-cli.jar --output ./tools/fhir-swagger-generator-4.11.1-cli.jar
}

function _generate_consumer_from_fhir() {
    rm ./swagger/consumer.yaml
    touch ./swagger/consumer.yaml
    java -jar ./tools/fhir-swagger-generator-4.11.1-cli.jar "DocumentReference(read,search)"
    yq -P ./openapi/DocumentReference-openapi.json > ./swagger/consumer.yaml
    rm -rf ./openapi/
}

function _generate_producer_from_fhir() {
    rm ./swagger/producer.yaml
    touch ./swagger/producer.yaml
    java -jar ./tools/fhir-swagger-generator-4.11.1-cli.jar "DocumentReference(read,search,create,update,delete)"
    yq -P ./openapi/DocumentReference-openapi.json > ./swagger/producer.yaml
    rm -rf ./openapi/
}

function _generate_from_fhir() {
    _get_generator
    _generate_consumer_from_fhir
    _generate_producer_from_fhir
    rm -rf ./tools/
}

function _generate_producer_model() {
    if [ ! -d "./layer/nrlf/nrlf/producer/fhir/r4" ]; then
        mkdir -p ./layer/nrlf/nrlf/producer/fhir/r4
    fi

    datamodel-codegen --input ./api/producer/swagger.yaml --input-file-type openapi --output ./layer/nrlf/nrlf/producer/fhir/r4/model.py --use-annotated --enum-field-as-literal all --use-double-quotes
}

function _generate_consumer_model() {
    if [ ! -d "./layer/nrlf/nrlf/consumer/fhir/r4" ]; then
        mkdir -p ./layer/nrlf/nrlf/consumer/fhir/r4
    fi

    datamodel-codegen --input ./api/consumer/swagger.yaml --input-file-type openapi --output ./layer/nrlf/nrlf/consumer/fhir/r4/model.py --use-annotated --enum-field-as-literal all --use-double-quotes
}

function _swagger() {
    local command=$1
    local type=$2
    case $command in
    "generate")
        if [[ -z "$type" ]]; then
            _generate_from_fhir
            (
                cd scripts
                python3 -c "import swagger_generator as sg; sg.entry()"
            )
            _generate_consumer_model
            _generate_producer_model
        else
            _get_generator
            if [ $type = 'consumer' ]; then
                _generate_consumer_from_fhir
                (
                    cd scripts
                    python3 -c "import swagger_generator as sg; sg.entry('$type')"
                )
                _generate_consumer_model
            elif [ $type = 'producer' ]; then
                _generate_producer_from_fhir
                (
                    cd scripts
                    python3 -c "import swagger_generator as sg; sg.entry('$type')"
                )
                _generate_producer_model
            else
                rm -rf ./tools/
                _nrlf_commands_help && return 1
            fi
            rm -rf ./tools/
        fi
        ;;
    "generate-swagger")
        if [[ -z "$type" ]]; then
            _generate_from_fhir
            (
                cd scripts
                python3 -c "import swagger_generator as sg; sg.entry()"
            )
        else
            _get_generator
            if [ $type = 'consumer' ]; then
                _generate_consumer_from_fhir
            elif [ $type = 'producer' ]; then
                _generate_producer_from_fhir
            else
                rm -rf ./tools/
                _nrlf_commands_help && return 1
            fi
            rm -rf ./tools/

            (
                cd scripts
                python3 -c "import swagger_generator as sg; sg.entry('$type')"
            )
        fi
        ;;
    "generate-model")
        if [[ -z "$type" ]]; then
            _generate_consumer_model
            _generate_producer_model
        else
            if [ $type = 'consumer' ]; then
                _generate_consumer_model
            elif [ $type = 'producer' ]; then
                _generate_producer_model
            else
                _nrlf_commands_help && return 1
            fi
        fi
        ;;
    "merge")
        allowed_types="producer consumer"
        local type=$2
        if [[ " ${allowed_types[*]} " =~ " $2 " ]]; then
            cat ./swagger/${type}.yaml |
                 # Replace snake case terms, which are invalid in ApiGateway
                yq 'with(.components.schemas; with_entries(.key |= sub("_","")))' |
                yq '(.. | select(has("$ref")).$ref) |= sub("_","")' |
                # Remove the parts we don't want
                yq 'del(.x-ibm-configuration)' |
                yq 'del(.components.schemas.*.discriminator)' \
                    > ./swagger/${type}.tmp.yaml

            # Merge in the narrative, and save for internal use (i.e. including status endpoint)
            yq eval-all '. as $item ireduce ({}; . * $item)' \
                ./swagger/${type}.tmp.yaml \
                ./swagger/${type}-static/*.yaml \
                > ./api/${type}/swagger.yaml

            # Remove fields not required for public docs (i.e. for the APIM/APIGEE repo)
            cat ./api/${type}/swagger.yaml |
                yq 'del(.paths.*.*.x-amazon-apigateway-integration)' |
                yq 'del(.paths.*.*.security)' |
                yq 'del(.paths./_status)' \
                    > ./api/${type}/swagger-public.yaml

            rm ./swagger/${type}.tmp.yaml
        else
            _swagger_help
        fi
        ;;
    *) _swagger_help ;;
    esac
}
