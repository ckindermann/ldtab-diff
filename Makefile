### Configuration
#
# These are standard options to make Make sane:
# <http://clarkgrubb.com/makefile-style-guide#toc2>

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.PRECIOUS:
.SUFFIXES:

export PATH := $(shell pwd)/bin:$(PATH)

DB := example/ldtab.db

### Main Tasks

.PHONY: help
help:
	@echo "LDTab Diff Example"
	@echo ""
	@echo "TASKS"
	@echo "  all         build all files"
	@echo "  clean       remove all build files"
	@echo "  clobber     remove all generated files"
	@echo "  help        print this message"

.PHONY: build
build: example/a.tsv example/b.tsv example/c.tsv example/diff/ab/ example/diff/bc/ example/fromLDTab/

.PHONY: all
all: build

.PHONY: clean
clean:
	rm -rf example/

.PHONY: clobber
clobber:
	rm -rf bin/ example/

bin/ example/:
	mkdir -p $@

### Install Dependencies

# Require SQLite
ifeq ($(shell command -v sqlite3),)
$(error 'Please install SQLite 3')
endif

# Require Java
ifeq ($(shell command -v java),)
$(error 'Please install Java, so we can run ROBOT and LDTab')
endif

# Require Python
ifeq ($(shell command -v python3),)
$(error 'Please install Python, so we can run LDTab-Diff')
endif

# Install LDTab (Clojure implementation)
bin/ldtab.jar: | bin/
	curl -L -o $@ 'https://github.com/ontodev/ldtab.clj/releases/download/v2023-12-21/ldtab.jar'

bin/ldtab: bin/ldtab.jar
	echo '#!/bin/sh' > $@
	echo 'java -jar "$$(dirname $$0)/ldtab.jar" "$$@"' >> $@
	chmod +x $@


### Convert Ontologies

$(DB): resources/prefix.tsv | bin/ldtab example/
	ldtab init $(DB) 
	ldtab prefix $(DB) $<
	ldtab import $(DB) resources/ontologies/a.xml

example/%.tsv: resources/ontologies/%.xml resources/prefix.tsv | $(DB)
	sqlite3 $(DB) 'DROP TABLE IF EXISTS $*'
	rm -f $@
	ldtab init $(DB) --table $*
	ldtab import $(DB) $< --table $*
	ldtab export $(DB) $@ --table $* --format tsv
	sqlite3 $(DB) 'DROP TABLE IF EXISTS $*'


### Compute Differences

example/diff/ab/: example/a.tsv example/b.tsv | $(DB)
	mkdir -p tmp
	mkdir -p example/diff/ab/
	test -d venv || python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 cli.py add-delta example/ldtab.db example/b.tsv
	mv tmp/* example/diff/ab/
	rmdir tmp

example/diff/bc/: example/b.tsv example/c.tsv | $(DB) example/diff/ab/
	mkdir -p tmp
	mkdir -p example/diff/bc/
	test -d venv || python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 cli.py add-delta example/ldtab.db example/c.tsv
	mv tmp/* example/diff/bc/
	rmdir tmp

### Build Ontologies from LDTab database

example/fromLDTab/: example/a.tsv example/b.tsv example/c.tsv | $(DB) example/diff/ab/ example/diff/bc/
	mkdir -p example/fromLDTab/
	test -d venv || python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 cli.py build example/ldtab.db 1 example/fromLDTab/1.tsv
	. venv/bin/activate && python3 cli.py build example/ldtab.db 2 example/fromLDTab/2.tsv
	. venv/bin/activate && python3 cli.py build example/ldtab.db 3 example/fromLDTab/3.tsv
