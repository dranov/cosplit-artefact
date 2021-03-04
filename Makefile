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
	rm -rf benchmarks/*.log
	rm -rf benchmarks/*.aux
	rm -rf benchmarks/*.pdf


.PHONY: benchmarks clean
