import sqlite3
import sys
import os

# from datetime import date
# from datetime import datetime
# import time
# import csv

################################
# General ######################
################################


def get_max_transaction(tsv):
    max = -1
    file = open(tsv, "r")
    next(file)  # skip header
    for line in file:
        # print(line)
        cols = line.split("\t")
        # print(cols)
        if int(cols[0]) > max:
            max = int(cols[0])

    return max


def get_max_transaction_database(connection):
    cur = connection.cursor()
    query = f"SELECT max(assertion) FROM statement"
    for row in cur.execute(query):
        return list(row.values())[0]


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def set_transaction_retraction(tsv, transaction, retract, out):
    input = open(tsv, "r")
    output = open(out, "a")
    for line in input:
        cols = line.split("\t")
        cols[0] = transaction  # set transaction id
        cols[1] = retract  # set assert(add)/retract(delete) column
        transformation = "\t".join(cols)
        output.write(transformation)
    input.close()
    output.close()


################################
# 1. Build #####################
################################

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


def encode_annotation(value):
    if value is None:
        return ""
    else:
        return str(value)


def encode_tsv_triple(triple):
    res = (
        str(triple["assertion"])
        + "\t"
        + str(triple["retraction"])
        + "\t"
        + triple["graph"]
        + "\t"
        + triple["subject"]
        + "\t"
        + triple["predicate"]
        + "\t"
        + triple["object"]
        + "\t"
        + triple["datatype"]
        + "\t"
        + encode_annotation(triple["annotation"])
    )
    return res


def build_to_transaction(connection, transaction, output):
    transactions = get_transactions(connection, transaction)

    # print(transactions)
    ontology = set()

    # start with smallest transaction
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
                ontology.add(encode_tsv_triple(triple))

            if triple["retraction"] == 1:

                triple["assertion"] = "1"
                triple["retraction"] = "0"
                ontology.remove(encode_tsv_triple(triple))

    # file = open(output + "-build-" + str(transaction) + ".tsv", "a")
    file = open(output, "a")
    file.write(
        "assertion"
        + "\t"
        + "retraction"
        + "\t"
        + "graph"
        + "\t"
        + "subject"
        + "\t"
        + "predicate"
        + "\t"
        + "object"
        + "\t"
        + "datatype"
        + "\t"
        + "annotation"
        "\n"
    )
    for axiom in ontology:
        file.write(axiom + "\n")
    file.close()


#################################
# 2. Diff #######################
#################################


# given tsv_1 and tsv_"
# compute the diff/delta between tsv_1 and tsv_2
# then add delta to tsv_1
# and store this in a new tsv
def compute_tsv_diff(tsv_1, tsv_2):

    # sort both files
    os.system("sort " + tsv_1 + ">> tmp/sort_1")
    os.system("sort " + tsv_2 + ">> tmp/sort_2")

    # compare both files using comm
    os.system("comm -23 tmp/sort_1 tmp/sort_2 >> tmp/deleted")
    os.system("comm -13 tmp/sort_1 tmp/sort_2 >> tmp/added")

    # delete sorted
    os.system("rm tmp/sort_1")
    os.system("rm tmp/sort_2")

    # TODO: how do we assign transaction ids:
    # - simple increments?
    # - dates?
    transaction_id = str(get_max_transaction(tsv_1) + 1)
    # now = datetime.now()
    # transaction_id = now.strftime("%Y%m%d%H%M%S")

    # save earlier version
    # TODO: this is not necessary? -- this will be refactored to tsv delta
    os.system("cp " + tsv_1 + " tmp/" + transaction_id + ".tsv")

    output = open("tmp/" + transaction_id + ".tsv", "a")
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


#################################
# 3. Delta ######################
#################################

# take an LDTab database as input
# build the most recent ontology version
# then compute the diff
# and then add the delta to the LDTab database
def add_tsv_delta(ldtab, new_tsv):
    # 1. built most recent version
    # 1.1 get most recent transaction number
    max_transaction = get_max_transaction_database(ldtab)

    # 1.2 use build command to build most recent ontology (serialise it as TSV)
    build_to_transaction(ldtab, max_transaction, "tmp/previous.tsv")

    # 2. comute diff
    # this will create:
    # - tmp/deleted
    # - tmp/added
    # - tmp/({max_transaction}+1)-previous-diff.tsv
    compute_tsv_diff("tmp/previous.tsv", new_tsv)

    # 3. add delta to LDTab database
    # use LDTab implementation to export to TSV (use external command to java.jar)
    # os.system("java -jar ldtab.jar export " + ldtab + "tmp/export.tsv")

    # add deleted + added to LDtab database
    os.system("cat tmp/added >> tmp/previous.tsv")
    os.system("cat tmp/deleted >> tmp/previous.tsv")

    # TODO convert from TSV back to sqlite with sqlite  (don't do this here)


#################################
# 4. Basic CLI ##################
#################################

# commands:
# 1. BUILD:
#    given an LDTab database, and a transaction id
#    => return/write the ontology at that point in tim
# 2. DELTA (uses build and diff?):
#    given an LDTab database, and an updated ontology (tsv)
#    => add the corresponding delta to the LDTab database
# 3. DIFF:
#    given two ontologies (tsv)
#    => compute their diff
if __name__ == "__main__":
    file_1 = sys.argv[1]
    file_2 = sys.argv[2]

    # get connection
    con = sqlite3.connect(file_1, check_same_thread=False)
    con.row_factory = dict_factory

    add_tsv_delta(con, file_2)

    # print(get_transactions(con, 1))

    # max_transaction = get_max_transaction_database(con)
    # print(max_transaction)

    # compute_tsv_diff(file_1, file_2)

    # path management
    # script_dir = os.getcwd()
    # abs_file_path = os.path.join(script_dir, file_1)

    # Later
    # Later
    # Later

    # !!! example for BUILD command !!!
    # get_transactions(con, 99999999999)
    # build_to_transaction(con, 99294, destination)

    # triples.to_csv(
    #    "uuu",
    #    sep="\t",
    #    index=False,
    #    quoting=csv.QUOTE_NONE,
    #    doublequote=False,
    #    escapechar="\\",
    # )

    # f1 = open(file_1, "r")
    # file1 = set(f1.read().splitlines())
    # for line in file1:
    #    print(line)
