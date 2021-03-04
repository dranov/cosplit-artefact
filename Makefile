all: default

default: benchmarks
        
benchmarks:
	mkdir fig; \
	cd ./benchmarks; \
	./goodenough.sh > ./goodenough.csv; \
	Rscript goodenough_plots.r

	cd ./benchmarks; \
	./timing.sh > ./timing.csv; \
	pdflatex timing.tex; \
	mv timing.pdf ../fig/

clean:
	rm -rf fig/
	rm -rf benchmarks/*.csv

.PHONY: benchmarks clean
