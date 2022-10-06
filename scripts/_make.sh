function _make_help() {
    echo
    echo "sods make <command> [options]"
    echo
    echo "commands:"
    echo "  help          - this help screen"
    echo "  build         - Builds the code"
    echo "  clean         - Cleans the artefacts"
}

function _make() {
    command=$1
    case $command in
        "build") find $root -name make.sh | xargs -I % /bin/bash -c 'cd $(dirname %) && ./make.sh build' ;;
        "clean") find $root -name make.sh | xargs -I % /bin/bash -c 'cd $(dirname %) && ./make.sh clean' ;;
        "*") echo "Unhandled command: $command" ;;
    esac
}
