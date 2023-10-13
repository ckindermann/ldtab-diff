import click
import sqlite3
from diff import generate, util, compare, delta

@click.group()
def main():
    pass

@main.command()
@click.argument('database', type=str, required=True)
@click.argument('transaction', type=str, required=True)
@click.argument('output', type=str, required=True)
def build(database, transaction, output):

    """Building an ontology/graph to a specific version (transaction) in its editing history of an LDTab database."""
    # get connection
    con = sqlite3.connect(database, check_same_thread=False)
    con.row_factory = util.dict_factory

    click.echo(f"Saving ontology with transaction {transaction} in database {database} to {output}")
    generate.build_to_transaction(con, int(transaction), output)

#TODO
@main.command()
@click.argument('ontology', type=str, required=True)
@click.argument('patch', type=str, required=True)
@click.argument('output', type=str, required=True)
def apply(count):
    """This is subcommand 2."""
    click.echo("The command 'apply' is currently not supported")

@main.command()
@click.argument('database', type=str, required=True)
@click.argument('output', type=str, required=True)
def dump(database, output):
    """Export an LDTab database to TSV"""

    click.echo(f"Exporting {database} (LDTab) to {output} (TSV)")

    # get rows
    con = sqlite3.connect(database, check_same_thread=False)
    con.row_factory = util.dict_factory
    c = con.cursor()
    c.execute('SELECT * FROM statement')
    rows = c.fetchall()

    # write rows
    out = open(output, "a")
    for row in rows:
        out.write(util.encode_row(row) + "\n")
    out.close()

@main.command()
@click.argument('tsv1', type=str, required=True)
@click.argument('tsv2', type=str, required=True)
def diff(tsv1, tsv2):
    """Compute the diff between two TSV files and write the output to /tmp"""
    click.echo(f"Compute diff between {tsv1} with {tsv2} and store in /tmp")
    compare.compute_tsv_diff(tsv1, tsv2)

@main.command()
@click.argument('database', type=str, required=True)
@click.argument('tsv', type=str, required=True)
def add_delta(database, tsv):
    """Add the delta between an ontology/graphs's most recent version stored in a LDTab database and a new version (in TSV)"""
    click.echo(f"Add the delta between the most recent version in {database} and the new version {tsv}.")

    con = sqlite3.connect(database, check_same_thread=False)
    con.row_factory = util.dict_factory

    delta.add_tsv_delta(con, tsv)

if __name__ == '__main__':
    main()
