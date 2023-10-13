import sqlite3
import sys
import os
import csv

# from datetime import date
# from datetime import datetime
import time

def get_max_transaction(tsv):
    max = -1
    file = open(tsv, "r")
    # next(file)  # skip header
    for line in file:
        cols = line.split("\t")
        if(cols[0] == "assertion"): #TODO: not sure why header isn't skipped..
            continue
        if int(cols[0]) > max:
            max = int(cols[0])

    file.close()
    return max
#Given an LDTab ontology and a patch in terms of added and deleted statements,
#apply the patch to the ontology

def apply_patch(tsv, patch):

    transaction_id = str(get_max_transaction(tsv) + 1)
    os.system("cp " + tsv + " tmp/" + transaction_id + ".tsv")
