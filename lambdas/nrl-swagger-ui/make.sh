function _help() {
    echo
    echo "Usage: make.sh <command>"
    echo
    echo "Commands:"
    echo "  clean   - clean up any build artefacts"
    echo "  build   - build the lambda distribution"
    echo
}

function _clean() {
    echo "Cleaning swagger-ui"
    rm -rf ./api
    rm -rf ./dist
}

function _build() {
    echo "Building swagger-ui"
    mkdir -p ./dist
    npm install > /dev/null
    _prepare
    zip -r ./dist/swagger-ui.zip ./src/ ./api ./node_modules/ ./index.js package.json > /dev/null
}

function _prepare() {
    mkdir -p ./api
    cp ../../api/producer/nrl-producer-api.yaml ./api
    cp ../../api/consumer/nrl-consumer-api.yaml ./api
}


command=$1
args=(${@:2})

case $command in
    "clean") _clean $args ;;
    "build") _build $args ;;
    "prepare") _prepare $args ;;
    *) _help ;;
esac
