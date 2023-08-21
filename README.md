# ldtab-diff

LDTab-Diff is a tool for diffing and updating LDTab databases w.r.t. such diffs.

## General Concepts

An LDTab database encodes the editing history of an OWL ontology.
So, an LDTab database is *not an ontology*.
However, an LDTab database can be used to reconstruct an OWL ontology up to a point in its editing history.
Specifically, if an LDTab database only encodes *one* point in the editing history of an ontology,
then such a database *can be interpreted* in terms of a serialization format for an OWL ontology.

To make this distinction clear, we will refer to an LDTab database that can be interpreted as an OWL ontology as an LDTab ontology.
(Note that an LDTab ontology is an LDTab database but not every LDTab database is an LDTab ontology).

## Build

Build an LDTab ontology from an LDTab database up to the transaction `point-in-history`:

`build ldtab-database point-in-history output`

The resulting LDTab ontology will be written to `output`.

## Diff

Compute the diff between two LDTab ontologies:

`diff ontology-1 ontology-2 output`

The diff between the two ontologies will be written to `output`.

## Delta

Add the diff between the most recent LDTab ontology encoded in an LDTab database and an input LDTab ontology
to the LDTab database:

`add-delta database ontology`

This does the following:
1. Build the most recent LDTab ontology `recent` encoded in the input `database`
2. Compute the diff between `recent` and `ontology`
3. Add this diff to `database` as a new point in the editing history.
