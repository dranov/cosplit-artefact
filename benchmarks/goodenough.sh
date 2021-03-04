#!/bin/bash
SCILLA_PATH=/home/pldi21/scilla
CONTRACTS_PATH=/home/pldi21/cosplit-artefact/contracts

# CSV header
echo "Name,Line count,Trans,MaxGESize,ShardingRatio,MaxGENum,SEP,GE-1,GE-2,GE-3,GE-4,GE-5,GE-6,GE-7,GE-8,GE-9,GE-10,GE-11,GE-12,GE-13,GE-14,GE-15,GE-16,GE-17,GE-18,GE-19,SEP,Maximal selections"

for file in $CONTRACTS_PATH/*
do
line_count=$(wc -l "$file" | cut -d ' ' -f 1)
analysis=$($SCILLA_PATH/bin/scilla-checker -gaslimit 10000 -libdir $SCILLA_PATH/src/stdlib/ "$file" -sa -sa-ge 2> /dev/null | head -n 1 | sed 's/\[GoodEnough\] //' )
name=$(basename $file .scilla)
echo "$name, $line_count, $analysis"
done
