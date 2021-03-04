all: default

default: benchmarks
        
benchmarks:
	mkdir fig; \
	cd ./benchmarks; \
	./goodenough.sh > ./goodenough.csv; \
	Rscript goodenough_plots.r

clean:
	rm -rf fig/
	rm -rf benchmarks/goodenough.csv

.PHONY: benchmarks clean
