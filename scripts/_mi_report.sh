#!/bin/bash

function _mi_report() {
    poetry run python -m mi.reporting.report $1 $2
}
