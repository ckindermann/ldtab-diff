import sqlite3
import sys

# this expects a moment in time and
# then builds the ontology up until that moment in time


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# get all transaction id's that are smaller than the input
def get_transactions(connection, transaction):
    cur = connection.cursor()

    query = f"SELECT DISTINCT assertion FROM statement"

    ids = []
    for row in cur.execute(query):
        ids.append(row["assertion"])

    selection = []
    for id in ids:
        # TODO sort out datatypes
        if str(id) < str(transaction):
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


def build_to_transaction(database, transaction, output):
    transactions = get_transactions(database, transaction)

    print(transactions)
    ontology = set()

    # start with smallest transaction
    for t in transactions:
        # get all assertions
        triples = get_triples(database, str(t))
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

    file = open(output + "-build-" + transaction + ".tsv", "a")
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

    # create new database
    # con = sqlite3.connect("test_data.db", check_same_thread=False)
    # c = con.cursor()
    # c.execute("""CREATE TABLE ldtab ([key] TEXT PRIMARY KEY, [value] TEXT)""")
    # c.execute(
    #    """CREATE TABLE prefix ([prefix] TEXT PRIMARY KEY, [base] TEXT NOT NULL)"""
    # )
    # c.execute(
    #    """CREATE TABLE statement ([assertion] int NOT NULL, [retraction] int NOT NULL, [graph] TEXT NOT NULL, [subject] TEXT NOT NULL, [predicate] TEXT  NOT NULL, [object] TEXT NOT NULL, [datatype] TEXT NOT NULL, [annotation] TEXT)"""
    # )

    # c.execute(
    #    """INSERT INTO ldtab (key, value) VALUES ('ldtab version', '0.0.1'),  ('schema version', '0')""")

    # for axiom in ontology:
    #    c.execute(
    #        """INSERT INTO statement (assertion, retraction, graph, subject, predicate, object, datatype, annotation) VALUES ("""
    #        + str(axiom["assertion"])
    #        + ", "
    #        + axiom["retraction"]
    #        + ", "
    #        + axiom["graph"]
    #        + ", "
    #        + axiom["subject"]
    #        + ", "
    #        + axiom["predicate"]
    #        + ", "
    #        + axiom["object"]
    #        + ", "
    #        + axiom["datatype"]
    #        + ", "
    #        + axiom["annotation"]
    #        + ")"
    #    )

    # con.commit()


if __name__ == "__main__":

    database = sys.argv[1]
    transaction = sys.argv[2]
    output = sys.argv[3]

    con = sqlite3.connect(database, check_same_thread=False)
    con.row_factory = dict_factory

    build_to_transaction(con, transaction, output)
