#!/usr/bin/env sh
set -ex

for version in 2.7 3.5 3.6 3.7; do
    pyenv install \
        $(pyenv install --list | awk "\$1 ~ /^${version}/ && \$1 !~ /rc/ {print \$1}" | sort -V | tail -n1)
done
