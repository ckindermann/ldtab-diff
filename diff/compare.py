import sqlite3
import sys
import os
import csv

from diff import util

# given tsv_1 and tsv_2
# compute the diff/delta between tsv_1 and tsv_2:
# - added (asserted)
# - deleted (retracted)
#
def compute_tsv_diff(tsv_1, tsv_2):

    # sort both files
    os.system("sort " + tsv_1 + ">> tmp/sort_1")
    os.system("sort " + tsv_2 + ">> tmp/sort_2")

    # report duplicate rows 
    os.system("uniq -dc tmp/sort_1 >> tmp/duplicates_1 ")
    os.system("uniq -dc tmp/sort_2 >> tmp/duplicates_2 ")

    # remove them using uniq
    os.system("uniq tmp/sort_1 >> tmp/uniq_1 ")
    os.system("uniq tmp/sort_2 >> tmp/uniq_2 ")

    # compare both files using comm
    os.system("comm -13 tmp/uniq_1 tmp/uniq_2 >> tmp/added")
    os.system("comm -23 tmp/uniq_1 tmp/uniq_2 >> tmp/deleted")

    # delete sorted
    os.system("rm tmp/sort_1")
    os.system("rm tmp/sort_2")

    # delete uniq files
    os.system("rm tmp/uniq_1")
    os.system("rm tmp/uniq_2")

    # TODO: how do we assign transaction ids:
    # - simple increments?
    transaction_id = str(util.get_max_transaction(tsv_1) + 1)
    # - dates?
    # now = datetime.now()
    # transaction_id = now.strftime("%Y%m%d%H%M%S")

    output = open("tmp/patch.tsv", "a")
    added = open("tmp/added", "r")
    deleted = open("tmp/deleted", "r")

    # add new assertions
    for line in added:
        cols = line.split("\t")
        cols[0] = transaction_id  # set transaction id
        cols[1] = "0"  # set assert(add)/retract(delete) column
        transformation = "\t".join(cols)
        output.write(transformation)

    # add retractions
    for line in deleted:
        cols = line.split("\t")
        cols[0] = transaction_id  # set transaction id
        cols[1] = "1"  # set assert(add)/retract(delete) column
        transformation = "\t".join(cols)
        output.write(transformation)

    output.close()
    added.close()
    deleted.close()
