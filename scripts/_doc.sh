function _doc_help() {
    echo
    echo "nrlf doc <command>"
    echo
    echo "commands:"
    echo "  help                - this help screen"
    echo "  clean               - delete the generated docs"
    echo "  generate [<style>]  - OPTIONAL style to be used ('default' if unspecified)."
    echo "                        See https://pygments.org/styles/"
    echo "  push <name>         - push the documentation to confluence, grouped under '<name> - NRLF'"
    echo "                        e.g. 'dev' => 'dev - NRLF'"
    echo
    return 1
}

function _doc_clean() {
    echo "Cleaning..."
    rm -rf ./report
    echo "Cleaned..."
}

function _doc_generate() {
    local style=$1
    if [[ $# = 0 ]]; then
        style=default
    fi
    PYTHONPATH=packages python packages/feature_documentation/cli.py generate $style
}

function _doc_publish() {
    local env=$1
    if [[ $# = 0 ]]; then
        env=dev
    fi
    PYTHONPATH=packages python packages/feature_documentation/cli.py push $env
}

function _doc() {
    local command=$1
    local args=(${@:2})

    case $command in
        "clean") _doc_clean $args ;;
        "generate") _doc_generate $args ;;
        "push") _doc_publish $args ;;
        *) _doc_help $args ;;
    esac
}
