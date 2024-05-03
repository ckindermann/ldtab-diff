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

DB := build/ldtab.db

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

.PHONY: example
example: build/a.tsv build/b.tsv build/c.tsv build/diff/ab/ build/diff/bc/ build/fromLDTab/

.PHONY: all
all: example

.PHONY: clean
clean:
	rm -rf build/

.PHONY: clobber
clobber:
	rm -rf bin/ build/

bin/ build/:
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

$(DB): resources/prefix.tsv | bin/ldtab build/
	ldtab init $(DB) 
	ldtab prefix $(DB) $<
	ldtab import $(DB) resources/ontologies/a.xml

build/%.tsv: resources/ontologies/%.xml resources/prefix.tsv | $(DB)
	sqlite3 $(DB) 'DROP TABLE IF EXISTS $*'
	rm -f $@
	ldtab init $(DB) --table $*
	ldtab import $(DB) $< --table $*
	ldtab export $(DB) $@ --table $* --format tsv
	sqlite3 $(DB) 'DROP TABLE IF EXISTS $*'


### Compute Differences

build/diff/ab/: build/a.tsv build/b.tsv | $(DB)
	mkdir -p tmp
	mkdir -p build/diff/ab/
	test -d venv || python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 cli.py add-delta build/ldtab.db build/b.tsv
	mv tmp/* build/diff/ab/
	rmdir tmp

build/diff/bc/: build/b.tsv build/c.tsv | $(DB) build/diff/ab/
	mkdir -p tmp
	mkdir -p build/diff/bc/
	test -d venv || python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 cli.py add-delta build/ldtab.db build/c.tsv
	mv tmp/* build/diff/bc/
	rmdir tmp

### Build Ontologies from LDTab database

build/fromLDTab/: build/a.tsv build/b.tsv build/c.tsv | $(DB) build/diff/ab/ build/diff/bc/
	mkdir -p build/fromLDTab/
	test -d venv || python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 cli.py build build/ldtab.db 1 build/fromLDTab/1.tsv
	. venv/bin/activate && python3 cli.py build build/ldtab.db 2 build/fromLDTab/2.tsv
	. venv/bin/activate && python3 cli.py build build/ldtab.db 3 build/fromLDTab/3.tsv
