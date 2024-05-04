# ldtab-diff

LDTab-Diff is a tool for diffing ontologies and updating LDTab databases w.r.t. such diffs.

## tl;dr

- This is an experimental prototype to showcase LDTab's diffing capabilities
- `make all` simulates an example scenario involving three versions of an ontology. The following steps are executed: 
  1. install LDTab
  2. initialize an LDTab database (located in `example/ldtab.db`)
  3. ingest the three versions `a`, `b`, and `c` of an example ontology (located in `resources/ontologies`) into `example/ldtab.db`
  4. write the diffs between the three ontology versions to `example/diff`
  5. re-create the three input ontology versions using `example/ldtab.db` (generated files are in `example/fromLDTab`)
- You can play around with different ontology versions. Simply replace the contents of the example ontologies `resources/ontologies/*.xml`.

## General Concepts

An LDTab database encodes the editing history of an OWL ontology.
So, an LDTab database is *not an ontology*.
However, an LDTab database can be used to reconstruct an OWL ontology up to a point in its editing history.
Specifically, if an LDTab database only encodes *one* point in the editing history of an ontology,
i.e., the database only contains database entries about asserted facts at the given point in time,
then such a database *can be interpreted* in terms of a serialization format for an OWL ontology.

To make this distinction clear, we will refer to an LDTab database that can be interpreted as an OWL ontology as an LDTab ontology.
(Note that an LDTab ontology is an LDTab database but not every LDTab database is an LDTab ontology).

## Build

Build an LDTab ontology from an LDTab database up to the transaction `point-in-history`:

`python3 cli.py build ldtab-database point-in-history output`

The resulting LDTab ontology will be written to `output`.

## Diff

Compute the diff between two LDTab ontologies:

`python3 cli.py diff ontology-1 ontology-2`

The diff between the two ontologies will be written to the folder `./tmp`.
A diff includes the following files:

- `added`: LDTab rows that are in `ontology-2` but not in `ontology-1`
- `deleted`: LDTab rows that are in `ontology-1` but not in `ontology-2`
- `duplicates\_1` : duplicated rows in `ontology-1`
- `duplicates\_2` : duplicated rows in `ontology-2`
- `patch.tsv` : rows that represent the diff between the two ontology versions in an LDTab database

## Delta

Add the diff between the most recent LDTab ontology encoded in an LDTab database and an input LDTab ontology
to the LDTab database:

`python3 cli.py add-delta database ontology`

This does the following:
1. Build the most recent LDTab ontology `recent` encoded in the input `database`
2. Compute the diff between `recent` and `ontology`
3. Add this diff to `database` as a new point in the editing history.
