#create pdf: make main.pdf
%.pdf : %.tex
	rm -f $@
	pdflatex -shell-escape $< -o $@ 2>&1 | tee errors.err
#clean
	rm -f *.o errors.err
	rm -f *.aux *.bbl *.blg *.log *.out
	rm -f *.synctex.gz
	rm -f BUILD
	@echo
