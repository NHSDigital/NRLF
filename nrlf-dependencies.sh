#!/bin/bash

while read dep; do
    lib="${dep% *}"
    asdf plugin add ${lib}
done < .tool-versions

asdf install
