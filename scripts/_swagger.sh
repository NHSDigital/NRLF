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

    datamodel-codegen --input ./api/producer/swagger.yaml --input-file-type openapi --output ./layer/nrlf/nrlf/producer/fhir/r4/model.py --use-annotated --enum-field-as-literal all
}

function _generate_consumer_model() {
    if [ ! -d "./layer/nrlf/nrlf/consumer/fhir/r4" ]; then
        mkdir -p ./layer/nrlf/nrlf/consumer/fhir/r4
    fi

    datamodel-codegen --input ./api/consumer/swagger.yaml --input-file-type openapi --output ./layer/nrlf/nrlf/consumer/fhir/r4/model.py --use-annotated --enum-field-as-literal all
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
            # Remove the parts we don't want
            cat ./swagger/${type}.yaml |
                yq e 'del(.x-ibm-configuration)' |
                yq e 'del(.components.schemas.*.discriminator)' \
                    > ./swagger/${type}-static/clean.yaml

            # Merge in the narrative
            yq eval-all '. as $item ireduce ({}; . * $item)' \
                ./swagger/${type}-static/clean.yaml \
                ./swagger/${type}-static/*.yaml \
                > ./swagger/nrl-${type}-api.yaml

            rm ./swagger/${type}-static/clean.yaml
        else
            _swagger_help
        fi
        ;;
    *) _swagger_help ;;
    esac
}
