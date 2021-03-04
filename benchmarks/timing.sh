#!/bin/bash
SCILLA_PATH=/home/pldi21/scilla
CONTRACTS_PATH=/home/pldi21/cosplit-artefact/contracts
NUM_RUNS=100

# CSV header
echo "Name,LOC,Parse_min,Parse_avg,Parse_max,Typecheck_min,Typecheck_avg,Typecheck_max,Analysis_min,Analysis_avg,Analysis_max,Total_avg_w/o_analysis,Total_avg_w/_analysis,Avg_overhead_added_by_analysis,Avg_overhead_percent"

for file in $CONTRACTS_PATH/*
do
	name=$(basename $file | cut -d '~' -f 1)
	line_count=$(wc -l "$file" | cut -d ' ' -f 1)
	TMP_FILE="./_$name.csv"
	rm -f $TMP_FILE
	
	analysis=$($SCILLA_PATH/bin/scilla-checker -gaslimit 10000 -libdir $SCILLA_PATH/src/stdlib/ "$file" -sa -sa-timings 2>/dev/null | head -n3 | sed 's/\[Parse\] //' | sed 's/\[Typecheck\] '// | sed 's/\[Sharding\] //' | tr '\n' ',' | sed 's/,$//')
	if [[ $? -eq 0 ]]
	then
	for run in $(seq $NUM_RUNS)
	do
	analysis=$($SCILLA_PATH/bin/scilla-checker -gaslimit 10000 -libdir $SCILLA_PATH/src/stdlib/ "$file" -sa -sa-timings 2>/dev/null | head -n3 | sed 's/\[Parse\] //' | sed 's/\[Typecheck\] '// | sed 's/\[Sharding\] //' | tr '\n' ',' | sed 's/,$//')
	echo "$analysis" >> $TMP_FILE 
	done
	
	parse="cut -d , -f 1 $TMP_FILE"
	check="cut -d , -f 2 $TMP_FILE"
	shard="cut -d , -f 3 $TMP_FILE"
	
	awk=$'awk \'{if(min==""){min=max=$1}; if($1>max) {max=$1}; if($1<min) {min=$1}; total+=$1; count+=1} END {print min,"," total/count,"," max}\''
	parse=$(eval "$parse | $awk")
	check=$(eval "$check | $awk")
	shard=$(eval "$shard | $awk")

	echo "$name, $line_count, $parse, $shard, $parse"
	fi

done
