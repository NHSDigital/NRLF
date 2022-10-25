#!/bin/bash

function _swagger_help() {
    echo
    echo "nrlf swagger <command> [options]"
    echo
    echo "commands:"
    echo "  help                        - this help screen"
    echo "  generate <options>          - generate all swagger or producer/consumer if specified"
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
    java -jar ./tools/fhir-swagger-generator-4.11.1-cli.jar "DocumentReference(create,update,delete)"
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
        if [[ -z "$type" ]];
        then
            _generate_from_fhir
            (cd scripts ; python3 -c "import swagger_generator as sg; sg.entry()")
        else
            echo $type
            _get_generator
            if [ $type = 'consumer' ]
            then
                _generate_consumer_from_fhir
            elif [ $type = 'producer' ]
            then
                _generate_producer_from_fhir
            else
                rm -rf ./tools/
                _nrlf_commands_help && return 1
            fi
            rm -rf ./tools/

            (cd scripts ; python3 -c "import swagger_generator as sg; sg.entry('$type')")
        fi
        ;;
        *) _swagger_help ;;
    esac
}
