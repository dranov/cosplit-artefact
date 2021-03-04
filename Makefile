all: default

default: benchmarks
        
benchmarks:
	mkdir -p fig; \
	cd ./benchmarks; \
	./goodenough.sh | tee ./goodenough.csv; \
	Rscript goodenough_plots.r

	cd ./benchmarks; \
	./timing.sh | tee ./_timing.csv; \
	csvsort -c4 -r _timing.csv > timing.csv; \
	pdflatex timing.tex; \
	mv timing.pdf ../fig/

clean:
	rm -rf fig/
	rm -rf benchmarks/*.csv
	rm -rf benchmarks/*.log
	rm -rf benchmarks/*.aux
	rm -rf benchmarks/*.pdf


.PHONY: benchmarks clean
