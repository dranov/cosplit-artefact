#!/bin/bash
SCILLA_PATH=/home/pldi21/scilla

for file in $1
do
line_count=$(wc -l "$file" | cut -d ' ' -f 1)
analysis=$($SCILLA_PATH/bin/scilla-checker -gaslimit 10000 -libdir $SCILLA_PATH/src/stdlib/ "$file" -sa -sa-ge 2> /dev/null | head -n 1 | sed 's/\[GoodEnough\] //' )
echo "$file, $line_count, $analysis"
done