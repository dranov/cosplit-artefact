all: default

default: benchmarks
	
benchmarks: ./benchmarks/goodenough.sh ./benchmarks/goodenough_plots.r
	cd ./benchmarks
	./goodenough.sh > ./goodenough.csv
	Rscript goodenough_plots.r

clean:
	rm -rf fig/
	rm -rf benchmarks/goodenough.csv

.PHONY: coq clean install doc iris