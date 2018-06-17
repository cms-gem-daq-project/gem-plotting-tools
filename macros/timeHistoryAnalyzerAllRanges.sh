#! /usr/bin/env bash

function usage()
{
    echo >&2 'Usage: $1 <args...>'
    echo >&2 '    All arguments are passed to timeHistoryAnalyzer.py'
    echo >&2 '    Arguments may not contain --ranges'
    echo >&2
    echo >&2 'timeHistoryAnalyzer.py usage:'
    echo >&2
    timeHistoryAnalyzer.py -h
    kill -INT $$;
}

# Check if the argument list contains -h or --help
all_args=( "$@" ) # Save argument list as an array
while test $# -gt 0
do
    case "$1" in
        -h|--help)
            usage
            ;;
        --ranges*)
            echo >&2 'Error: --ranges found in arguments'
            usage
            ;;
    esac
    shift
done

for ranges in mask maskReason zeroInputCap; do
    set -e -o pipefail
    timeHistoryAnalyzer.py "${all_args[@]}" --ranges "$ranges" | tee "timeHistoryAnalyzerOutput_ranges_$ranges.txt"
    echo >&2 "Created timeHistoryAnalyzerOutput_ranges_$ranges.txt"
done
