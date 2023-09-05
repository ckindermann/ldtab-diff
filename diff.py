import sqlite3
import sys
import os
import csv

# from datetime import date
# from datetime import datetime
import time
from ast import literal_eval


################################
# General ######################
################################

#def get_max_transaction(tsv):
#    max = -1
#    with open(tsv, 'r') as tsv_file:
#        tsv_reader = csv.reader(tsv_file, delimiter='\t')
#        next(tsv_reader)  # skip header
#        for row in tsv_reader:
#            if int(row[0]) > max:
#                max = int(row[0])
#    return max



def get_repr(s):
     #return repr(str(s))[1:-1]
     if s is None :
         return ""
     escape_sequences = {
             '"': '\\"',    
             "'": "\\'",   
             '\n': '\\n', 
             '\t': '\\t',
             '\r': '\\r'
             #'\\': '\\\\',    TODO
             # Add more escape sequences as needed
             }
     # Iterate through the dictionary and apply the escapes
     for char, escape_sequence in escape_sequences.items():
         s = s.replace(char, escape_sequence)

     return s

def inv_repr(s):
    #if s != "":
    #    return literal_eval("'" + s + "'")
    #else:
    #    return s
    escape_sequences = {
            #'\\\\': '\\',   # Backslash TODO: 
             '\\"': '"',     # Double quotation mark
             "\\'": "'",     # Single quotation mark (apostrophe)
             '\\n': '\n',    # Newline
             '\\t': '\t',    # Tab
             '\\r': '\r'     # Carriage return
             # Add more escape sequences as needed
             }

     # Iterate through the dictionary and apply the escapes
    for char, escape_sequence in escape_sequences.items():
        s = s.replace(char, escape_sequence)

    return s



def encode_row(row):
    assertion = get_repr(str(row["assertion"]))
    retraction = get_repr(str(row["retraction"]))
    graph = get_repr(row["graph"])
    subject = get_repr(row["subject"])
    predicate = get_repr(row["predicate"])
    objec = get_repr(row["object"])
    datatype = get_repr(row["datatype"])
    annotation = get_repr(row["annotation"])


    encoding = assertion + "\t" + retraction + "\t" + graph + "\t" + subject + "\t" + predicate + "\t" + objec + "\t" + datatype + "\t" + annotation

    return encoding

def get_max_transaction(tsv):
    max = -1
    file = open(tsv, "r")
    next(file)  # skip header
    for line in file:
        cols = line.split("\t")
        if(cols[0] == "assertion"): #TODO: not sure why header isn't skipped..
            continue
        if int(cols[0]) > max:
            max = int(cols[0])

    file.close()
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
                ontology.add(encode_row(triple))

            if triple["retraction"] == 1:

                triple["assertion"] = "1"
                triple["retraction"] = "0"
                ontology.remove(encode_row(triple))

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
    # TODO: encode things with repr?
    for axiom in ontology:
        file.write(axiom + "\n")
    file.close()

#################################
# 2. Diff #######################
#################################

# given tsv_1 and tsv_2
# compute the diff/delta between tsv_1 and tsv_2:
# - added (asserted)
# - deleted (retracted)
#
def compute_tsv_diff(tsv_1, tsv_2):

    # sort both files
    os.system("sort " + tsv_1 + ">> tmp/sort_1")
    os.system("sort " + tsv_2 + ">> tmp/sort_2")

    # compare both files using comm
    os.system("comm -13 tmp/sort_1 tmp/sort_2 >> tmp/added")
    os.system("comm -23 tmp/sort_1 tmp/sort_2 >> tmp/deleted")

    # delete sorted
    os.system("rm tmp/sort_1")
    os.system("rm tmp/sort_2")

    # TODO: how do we assign transaction ids:
    # - simple increments?
    transaction_id = str(get_max_transaction(tsv_1) + 1)
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

#################################
# 3. Apply Patch ################
#################################


#Given an LDTab ontology and a patch in terms of added and deleted statements,
#apply the patch to the ontology

def apply_patch(tsv, patch):

    transaction_id = str(get_max_transaction(tsv) + 1)
    os.system("cp " + tsv + " tmp/" + transaction_id + ".tsv")
    # TODO add and delete statements from ontology
    # this would require iterating over the file and deleting a rows



#################################
# 4. Delta ######################
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
    # - tmp/({max_transaction}+1)-previous-diff.tsv (patch.tsv)
    compute_tsv_diff("tmp/previous.tsv", new_tsv)

    # 3. add delta to LDTab database
    # use LDTab implementation to export to TSV (use external command to java.jar)
    # os.system("java -jar ldtab.jar export " + ldtab + "tmp/export.tsv")

    # add deleted + added to LDtab database
    #TODO: insert into ldtab databse

    patch = open("tmp/patch.tsv", "r")
    cur = ldtab.cursor()

    for line in patch:
        cols = line.split("\t")


        query = "INSERT INTO statement VALUES ({}, {}, '{}', '{}', '{}', '{}', '{}', '{}')".format(int(cols[0]), int(cols[1]), cols[2],cols[3],cols[4],inv_repr(cols[5]).replace("'", "''"),cols[6],inv_repr(cols[7].rstrip('\n')).replace("'", "''"))

        cur.execute(query)


    ldtab.commit()
    patch.close()



def dump_db_2_tsv(database, output):

        con = sqlite3.connect(database, check_same_thread=False)
        con.row_factory = dict_factory
        c = con.cursor()
        c.execute('SELECT * FROM statement')

        rows = c.fetchall()

        out = open(output, "a")

        for row in rows:
            out.write(encode_row(row) + "\n")

        out.close()




#################################
# 5. Basic CLI ##################
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
    command = sys.argv[1]

    #works
    if command == "build":
        database = sys.argv[2]
        transaction_id = sys.argv[3]
        output = sys.argv[4]

        # get connection
        con = sqlite3.connect(database, check_same_thread=False)
        con.row_factory = dict_factory

        build_to_transaction(con, int(transaction_id), output)

    #works
    if command == "diff":
        file_1 = sys.argv[2]
        file_2 = sys.argv[3]
        #output = sys.argv[4]

        compute_tsv_diff(file_1, file_2)

    if command == "add-delta":
        database = sys.argv[2]
        ontology = sys.argv[3]

        con = sqlite3.connect(database, check_same_thread=False)
        con.row_factory = dict_factory

        add_tsv_delta(con, ontology)

    #works
    if command == "dump-tsv":
        database = sys.argv[2]
        output = sys.argv[3]
        dump_db_2_tsv(database, output)


        #csvWriter = csv.writer(open(output, "w"), delimiter='\t')
        #rows = c.fetchall()
        #print(len(rows))
        #csvWriter.writerows(rows)

    # print(get_transactions(con, 1))

    # max_transaction = get_max_transaction_database(con)
    # print(max_transaction)

    #compute_tsv_diff(file_1, file_2)

    # build(ldtab, transactionid, output)

    # path management
    # script_dir = os.getcwd()
    # abs_file_path = os.path.join(script_dir, file_1)

    # Later
    # Later
    # Later

    #40448

    
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
