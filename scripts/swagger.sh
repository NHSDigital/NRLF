#!/bin/bash

function _swagger_help() {
    echo
    echo "swagger.sh <command> [options]"
    echo
    echo "commands:"
    echo "  help                         - this help screen"
    echo "  generate <options>           - generate all swagger and models or producer/consumer if specified"
    echo "  generate-swagger <options>   - generate all swagger or producer/consumer if specified"
    echo "  merge <options>              - generates the record-locator/<type>.yml file"
    echo
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

function _swagger() {
    local command=$1
    local type=$2
    case $command in
    "generate")
        if [[ -z "$type" ]]; then
            echo "Type is required, must be either 'consumer' or 'producer'" 1>&2
            exit 1
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
    "merge")
        allowed_types="producer consumer"
        local type=$2
        if [[ " ${allowed_types[*]} " =~ " $2 " ]]; then
            set -x
            cat ./swagger/${type}.yaml |
                # Remove commented lines
                grep -v "^\s*#" |
                 # Replace snake case terms, which are invalid in ApiGateway
                yq 'with(.components.schemas; with_entries(.key |= sub("_","")))' |
                yq '(.. | select(has("$ref")).$ref) |= sub("_","")' |
                # Remove the parts we don't want
                yq 'del(.paths.*.post.requestBody.content."application/x-www-form-urlencoded")' |
                yq 'del(.x-ibm-configuration)' |
                yq 'del(.components.schemas.*.discriminator)' |
                yq '(.. | select(style == "single")) style |= "double"' \
                    > ./swagger/${type}.tmp.yaml
            set +x

            # Merge in the narrative, and save for internal use (i.e. including status endpoint)
            yq eval-all '. as $item ireduce ({}; . * $item)' \
                ./swagger/${type}.tmp.yaml \
                ./swagger/${type}-static/*.yaml \
                > ./api/${type}/swagger.yaml

            # Remove fields not required for public docs
            # * AWS specific stuff, including security & lambdas
            # * security tags
            # * API catalogue dislikes tags
            # * /_status not public
            cat ./api/${type}/swagger.yaml |
                yq 'with(.paths.*.*.responses.*.content; with_entries(.key |= . + ";version=1" ))' |
                yq 'with(.components.requestBodies.*.content; with_entries(.key |= . + ";version=1" ))' |
                yq 'with(.components.responses.*.content; with_entries(.key |= . + ";version=1" ))' |
                yq 'del(.paths.*.*.x-amazon-apigateway-integration)' |
                yq 'del(.paths.*.*.security)' |
                yq 'del(.tags)' |
                yq 'del(.paths.*.*.tags)' |
                yq 'del(.paths./_status)' |
                yq 'del(.components.securitySchemes."${authoriser_name}")' \
                    > ./api/${type}/record-locator/${type}.yaml

            rm ./swagger/${type}.tmp.yaml

            # Remove fields not valid on AWS but otherwise required in public docs
            # * 4XX codes
            cat ./api/${type}/swagger.yaml |
                yq 'del(.. | select(has("4XX")).4XX)' \
                    >  ./api/${type}/swagger-tmp.yaml
            mv ./api/${type}/swagger-tmp.yaml ./api/${type}/swagger.yaml

        else
            _swagger_help
        fi
        ;;
    *) _swagger_help ;;
    esac
}

_swagger "${@:1}"
