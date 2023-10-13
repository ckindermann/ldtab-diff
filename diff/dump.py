import sqlite3
from util import encode_row

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
