#!/bin/bash

echo "Time and Ouput Test: A simple script to keep track of execution time \
and returned output after refactoring and optimizing."
echo ""
echo "This script can test refactors and optimizations using all supported \
timeframes with the specified inputs."
echo ""

one_liner="envdir .env_sandbox python _cmd.py -i EUR_USD -i EUR_GBP -i USD_CAD -l warning"
log_files="ls ./logs | grep pyfx_debug"
store_files="ls ./tmp/stores | grep .h5"

# delete log files
for i in $( eval $log_files ); do
    rm ./logs/$i
done

# init info_file
info_file="./logs/test_out.txt"
rm $info_file
touch $info_file

declare -a start=("2015.07.15" "2016.01.20" "2016.02.20")
declare -a end=("2015.07.16" "2016.01.25" "2016.03.20")
declare -a length=("1" "5" "30")

# declare -a start=("2015.08.13")
# declare -a end=("2016.08.13")
# declare -a length=("365")

# begin for loop
for j in {0..2}; do
    echo "Running ${length[$j]} day test with optimizations..."
    echo "Running ${length[$j]} day test with optimizations..." >> $info_file
    echo "Start date is ${start[$j]}, end date is ${end[$j]}." >> $info_file
    eval $one_liner -s ${start[$j]} -e ${end[$j]}
done

# record data
for i in $( eval $log_files ); do
    echo "" >> $info_file
    head -n 30 ./logs/$i >> $info_file
    tail ./logs/$i >> $info_file
    echo "" >> $info_file
done
