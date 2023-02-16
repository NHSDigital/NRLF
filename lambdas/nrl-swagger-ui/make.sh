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
    rm -rf ./dist
}

function _build() {
    echo "Building swagger-ui"
    mkdir -p ./dist
    npm install > /dev/null
    zip -r ./dist/swagger-ui.zip ./src/ ./node_modules/ ./index.js package.json > /dev/null
}


command=$1
args=(${@:2})

case $command in
    "clean") _clean $args ;;
    "build") _build $args ;;
    *) _help ;;
esac
