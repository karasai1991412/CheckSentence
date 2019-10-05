#!/bin/bash
mode="predict"
mph="Model"
dsp="./data_all.csv"
dap="./taskA_answers_all.csv"
nlt=2000
epochs=3
n_lines=100
sentence="He drinks milk"
output="./"
while getopts m:p:s:a:l:e:n:t:o: option
do
case "${option}"
in
m) mode=${OPTARG};;
p) mph=${OPTARG};;
s) dsp=${OPTARG};;
a) dap=${OPTARG};;
l) nlt=${OPTARG};;
e) epochs=${OPTARG};;
n) n_lines=${OPTARG};;
t) sentence=${OPTARG};;
o) output=${OPTARG};;

esac
done
echo $sentence
cd main
./main --mode $mode --ModelPath $mph --linesToTrain $nlt --data_sent_path $dsp --data_answer_path $dap --epochs $epochs --n_lines $n_lines --sentence "$sentence" --data_output $output
