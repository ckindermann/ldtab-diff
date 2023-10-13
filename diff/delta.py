import sqlite3
import sys
import os
import csv

from diff import util, generate, compare


# from datetime import date
# from datetime import datetime
# take an LDTab database as input
# build the most recent ontology version
# then compute the diff
# and then add the delta to the LDTab database
def add_tsv_delta(ldtab, new_tsv):
    # 1. built most recent version
    # 1.1 get most recent transaction number
    max_transaction = util.get_max_transaction_database(ldtab)

    # 1.2 use build command to build most recent ontology (serialise it as TSV)
    generate.build_to_transaction(ldtab, max_transaction, "tmp/previous.tsv")

    # 2. compute diff
    # this will create:
    # - tmp/deleted
    # - tmp/added
    # - tmp/({max_transaction}+1)-previous-diff.tsv (patch.tsv)
    compare.compute_tsv_diff("tmp/previous.tsv", new_tsv)

    # 3. add delta to LDTab database
    # use LDTab implementation to export to TSV (use external command to java.jar)
    # os.system("java -jar ldtab.jar export " + ldtab + "tmp/export.tsv")

    # add deleted + added to LDtab database
    #TODO: insert into ldtab databse

    patch = open("tmp/patch.tsv", "r")
    cur = ldtab.cursor()

    for line in patch:
        cols = line.split("\t")


        query = "INSERT INTO statement VALUES ({}, {}, '{}', '{}', '{}', '{}', '{}', '{}')".format(max_transaction+1, int(cols[1]), cols[2],cols[3],cols[4],util.inv_repr(cols[5]).replace("'", "''"),cols[6],util.inv_repr(cols[7].rstrip('\n')).replace("'", "''"))

        cur.execute(query)


    ldtab.commit()
    patch.close()
