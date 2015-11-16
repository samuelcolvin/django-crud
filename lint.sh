#!/usr/bin/env bash
flake8 --max-line-length 120 --max-complexity 10  django_crud
flake1=$?
echo "flake django_crud exit code:  ${flake1}"
flake8 --max-line-length 120 --max-complexity 10  tests/
flake2=$?
echo "flake tests exit code:        ${flake2}"
flake8 --max-line-length 120 --max-complexity 10  example_site/
flake3=$?
echo "flake example_site exit code: ${flake3}"
exit $((${flake1} + ${flake2} + ${flake3}))
