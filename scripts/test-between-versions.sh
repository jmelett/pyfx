#!/bin/bash

echo "Time and Ouput Test: A simple script to keep track of execution time \
and returned output before and after a refactor and/or optimization."
echo ""
echo "This script can test refactors and optimizations using all supported \
timeframes with the specified inputs."
echo ""

one_liner="envdir .env_sandbox python _cmd.py -i EUR_USD -i EUR_GBP -i USD_CAD -l warning"
optimized_v="git checkout backtest_optimizations"
non_optimized_v="git checkout before-optimizations"
log_file="ls ./logs | grep pyfx_debug"
store_files="ls ./tmp/stores | grep .h5"

# delete stores and logs
for i in $( eval $store_files ); do
    rm ./tmp/stores/$i
done

for i in $( eval $log_file ); do
    rm ./logs/$i
done

# init info_file
info_file="./logs/test_out.txt"
rm $info_file
touch $info_file

declare -a start=("2015.07.15" "2016.01.20" "2016.02.20")
declare -a end=("2015.07.16" "2016.01.25" "2016.03.20")
declare -a length=("1" "5" "30")

# begin for loop
for j in {0..2}; do
    eval $optimized_v
    echo "Running ${length[$j]} day test with optimizations..."
    echo "Running ${length[$j]} day test with optimizations..." >> $info_file
    echo "Start date is ${start[$j]}, end date is ${end[$j]}." >> $info_file
    eval $one_liner -s ${start[$j]} -e ${end[$j]}

    # record data
    head -n 30 ./logs/$( eval $log_file ) >> $info_file
    tail ./logs/$( eval $log_file ) >> $info_file
    echo "" >> $info_file

    # delete stores and logs
    for i in $( eval $store_files ); do
        rm ./tmp/stores/$i
    done

    for i in $( eval $log_file ); do
        rm ./logs/$i
    done

    eval $non_optimized_v
    echo "Running ${length[$j]} day test without optimizations..."
    echo "Running ${length[$j]} day test without optimizations..." >> $info_file
    echo "Start date is ${start[$j]}, end date is ${end[$j]}." >> $info_file
    eval $one_liner -s ${start[$j]} -e ${end[$j]}

    # record data
    head -n 30 ./logs/$( eval $log_file ) >> $info_file
    tail ./logs/$( eval $log_file ) >> $info_file
    echo "" >> $info_file

    # delete stores and logs
    for i in $( eval $store_files ); do
        rm ./tmp/stores/$i
    done

    for i in $( eval $log_file ); do
        rm ./logs/$i
    done
done

# return to original branch
eval $optimized_v
