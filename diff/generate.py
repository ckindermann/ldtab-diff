import sqlite3
import sys
import os
import csv
from diff import util

# from datetime import date
# from datetime import datetime
import time

# get all transaction id's that are smaller (or equal to) than the input
def get_transactions(connection, transaction):
    cur = connection.cursor()

    query = f"SELECT DISTINCT assertion FROM statement"

    ids = []
    for row in cur.execute(query):
        ids.append(row["assertion"])

    selection = []
    for id in ids:
        # TODO: smaller equal?
        if id <= transaction:  # NB: both id and transaction are ints
            selection.append(id)

    selection.sort()
    return selection

def get_triples(connection, transaction):
    cur = connection.cursor()
    query = f"SELECT * FROM statement WHERE " f"assertion='{transaction}'"
    triples = []
    for row in cur.execute(query):
        triples.append(row)

    return triples

def build_to_transaction(connection, transaction, output):
    transactions = get_transactions(connection, transaction)

    ontology = set()

    # start with smallest transaction (transactions are sorted)
    for t in transactions:
        # get all assertions
        triples = get_triples(connection, str(t))
        for triple in triples:
            # add and delete things as required
            # NB: we type assertion and retraction as ints in the database
            # but we need to convert them to strings when working with TSVs
            if triple["retraction"] == 0:

                # need to keep transaction id the same in order to hash things
                triple["assertion"] = "1"
                triple["retraction"] = "0"
                ontology.add(util.encode_row(triple))

            if triple["retraction"] == 1:

                triple["assertion"] = "1"
                triple["retraction"] = "0"
                ontology.remove(util.encode_row(triple))

    # file = open(output + "-build-" + str(transaction) + ".tsv", "a")
    file = open(output, "a")

    for axiom in ontology:
        file.write(str(axiom) + "\n")
    file.close()
