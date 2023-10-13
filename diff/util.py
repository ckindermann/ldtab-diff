
def get_repr(s):
     #return repr(str(s))[1:-1]
     if s is None :
         return ""
     escape_sequences = {
             #'"': '\\"',    
             #"'": "\\'",   
             #'\\': '\\\\',
             '\n': '\\n', 
             '\t': '\\t',
             '\r': '\\r'
             # Add more escape sequences as needed
             }
     # Iterate through the dictionary and apply the escapes
     for char, escape_sequence in escape_sequences.items():
         s = s.replace(char, escape_sequence)

     return s

def inv_repr(s):
    escape_sequences = {
             #'\\\\': '\\',
             #'\\"': '"',
             #"\\'": "'",
             '\\n': '\n',
             '\\t': '\t',
             '\\r': '\r' 
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
    # next(file)  # skip header
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
