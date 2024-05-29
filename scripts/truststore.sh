#!/bin/bash
# Script to manage the NRLF truststore files
set -o errexit -o pipefail -o nounset

BUCKET="nhsd-nrlf--truststore"

function _truststore_help() {
    echo
    echo "$0 <command> [options]"
    echo
    echo "commands:"
    echo "  help                            - this help screen"
    echo "  build-ca <name> <fqdn>          - Build a single CA cert"
    echo "  build-cert <name> <ca> <fqdn>   - Build a single client cert + private key"
    echo "  build-all                       - Build the standard trust store certs"
    echo "  pull-ca <ca>                    - Pull the certificate authority"
    echo "  pull-client <env>               - pull the files needed for a client connection"
    echo "  pull-server <env>               - pull the files needed for a server connection"
    echo
}

# read an input file and substitute all the ${} entries
function substitute_env_in_file() {
    infile=$1
    outfile=$2

    output=$(eval "cat <<EOF
$(cat ${infile})
EOF"
)
    cat > ${outfile} <<EOF
${output}
EOF
}

# build a certificate authority
function _truststore_build_ca() {
    if [ $# -ne 2 ]; then
        echo "Usage: $0 build-ca <name> <fqdn>"
        exit 1
    fi

    ca=$1
    fqdn=$2

    substitute_env_in_file ./truststore/config/ca.conf /tmp/ca.conf

    echo -e "🚧 Building CA: $ca \t(FQDN: $fqdn)"

    openssl req -newkey rsa:4096 \
        -nodes \
        -keyout ./truststore/ca/$ca.key \
        -new \
        -x509 \
        -days 36500 \
        -out ./truststore/ca/$ca.crt \
        -config /tmp/ca.conf \
        -extensions v3_req \
        -extensions v3_ca &> /dev/null

    rm /tmp/ca.conf
    echo -e "✅ Successfully Built CA: $ca"
}

# buld a certificate
function _truststore_build_cert() {
    if [ $# -ne 3 ]; then
        echo "Usage: $0 build-cert <name> <ca> <fqdn>"
        exit 1;
    fi

    client=$1
    ca=$2
    fqdn=$3
    serial=$(date +%s%3N)

    substitute_env_in_file ./truststore/config/client.conf /tmp/client.conf

    echo -e "🚧 Generating $client keypair"

    openssl req \
        -newkey rsa:4096 \
        -nodes \
        -keyout truststore/client/$client.key \
        -new \
        -out truststore/client/$client.csr \
        -config /tmp/client.conf \
        -extensions v3_req \
        -extensions usr_cert &> /dev/null

    openssl x509 \
        -req \
        -in truststore/client/$client.csr \
        -CA truststore/ca/$ca.crt \
        -CAkey truststore/ca/$ca.key \
        -set_serial $serial \
        -out truststore/client/$client.crt \
        -days 36500 \
        -sha256 \
        -extfile /tmp/client.conf \
        -extensions v3_req \
        -extensions usr_cert &> /dev/null

    cat truststore/client/$client.crt truststore/ca/$ca.crt > truststore/server/$client.pem

    echo -e "✅ Successfully generated $client keypair"
    rm /tmp/client.conf
}


function _truststore_build_all() {
    _truststore_build_ca "prod" "record-locator.national.nhs.uk"
    _truststore_build_ca "int"  "record-locator.int.national.nhs.uk"
    _truststore_build_ca "ref"  "record-locator.ref.national.nhs.uk"
    _truststore_build_ca "qa"   "qa.record-locator.national.nhs.uk"
    _truststore_build_ca "dev"  "record-locator.dev.national.nhs.uk"

    _truststore_build_cert "prod" "prod" "api.record-locator.national.nhs.uk"
    _truststore_build_cert "int"  "int"  "int.api.record-locator.int.national.nhs.uk"
    _truststore_build_cert "ref"  "ref"  "ref.api.record-locator.ref.national.nhs.uk"
    _truststore_build_cert "qa"   "qa"   "api.qa.record-locator.national.nhs.uk"
    _truststore_build_cert "dev"  "dev"  "dev.api.record-locator.dev.national.nhs.uk"
}

function _truststore_pull_ca() {
    env=$1
    aws s3 cp "s3://${BUCKET}/ca/${env}.crt" "truststore/ca/${env}.crt"
}

function _truststore_pull_client() {
    env=$1
    aws s3 cp "s3://${BUCKET}/client/${env}.key" "truststore/client/${env}.key"
    aws s3 cp "s3://${BUCKET}/client/${env}.crt" "truststore/client/${env}.crt"
}

function _truststore_pull_server() {
    env=$1
    echo "Pulling truststore/server/${env}.pem"
    aws s3 cp "s3://${BUCKET}/server/${env}.pem" "truststore/server/${env}.pem"
}

function _truststore_pull_all() {
    env=$1
    _truststore_pull_ca $env
    _truststore_pull_client $env
    _truststore_pull_server $env
}

function _truststore() {
    local command=$1; shift
    local args=$@

    case $command in
        "build-all") _truststore_build_all $args ;;
        "build-ca") _truststore_build_ca $args ;;
        "build-cert") _truststore_build_cert $args ;;
        "pull-all") _truststore_pull_all $args ;;
        "pull-server") _truststore_pull_server $args ;;
        "pull-client") _truststore_pull_client $args ;;
        "pull-ca") _truststore_pull_server $args ;;
        *) _truststore_help $args ;;
    esac
}

_truststore $@
