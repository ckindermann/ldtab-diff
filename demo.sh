#!/bin/bash

mkdir -p demo

# Download ontologies: obi_1.owl (v2023-07-25) and obi_2.owl (v2023-09-20)

echo "#"
echo "# Downloading ontologies"
echo "#"

mkdir -p demo/ontologies
wget -O demo/ontologies/obi_1.owl https://raw.githubusercontent.com/obi-ontology/obi/v2023-07-25/obi.owl
wget -O demo/ontologies/obi_2.owl https://raw.githubusercontent.com/obi-ontology/obi/v2023-09-20/obi.owl
wget -O demo/ontologies/obi_3.owl https://raw.githubusercontent.com/obi-ontology/obi/v2024-01-09/obi.owl

# Transform ontologies: obi_1.tsv and obi_2.tsv

echo "#"
echo "# Transforming ontologies"
echo "#"

mkdir -p demo/ldtab

java -jar ldtab.jar init obi.db 
java -jar ldtab.jar prefix obi.db resources/prefix.tsv

java -jar ldtab.jar init obi.db --table obi_1
java -jar ldtab.jar init obi.db --table obi_2
java -jar ldtab.jar init obi.db --table obi_3

java -jar ldtab.jar import obi.db demo/ontologies/obi_1.owl --table obi_1
java -jar ldtab.jar import obi.db demo/ontologies/obi_2.owl --table obi_2
java -jar ldtab.jar import obi.db demo/ontologies/obi_3.owl --table obi_3

java -jar ldtab.jar export -l obi.db demo/ldtab/obi_1.tsv --table obi_1
java -jar ldtab.jar export -l obi.db demo/ldtab/obi_2.tsv --table obi_2
java -jar ldtab.jar export -l obi.db demo/ldtab/obi_3.tsv --table obi_3

sqlite3 obi.db 'DROP TABLE IF EXISTS obi_1'
sqlite3 obi.db 'DROP TABLE IF EXISTS obi_2'
sqlite3 obi.db 'DROP TABLE IF EXISTS obi_3'

# Compute deltas 

echo "#"
echo "# Computing deltas"
echo "#"

java -jar ldtab.jar import obi.db demo/ontologies/obi_1.owl 
python3 cli.py add-delta obi.db demo/ldtab/obi_2.tsv

mkdir -p demo/deltas/12
mv tmp/* demo/deltas/12

python3 cli.py add-delta obi.db demo/ldtab/obi_3.tsv

mkdir -p demo/deltas/23
mv tmp/* demo/deltas/23

# Re-create ontologies

echo "#"
echo "# Building ontologies from database"
echo "#"

mkdir -p demo/build
python3 cli.py build obi.db 2 demo/build/obi_2.tsv
python3 cli.py build obi.db 3 demo/build/obi_3.tsv

# sort TSVs

echo "#"
echo "# Sorting ontologies"
echo "#"

sort demo/ldtab/obi_2.tsv > demo/ldtab/obi_2_sorted.tsv
sort demo/ldtab/obi_3.tsv > demo/ldtab/obi_3_sorted.tsv

sort demo/build/obi_2.tsv > demo/build/obi_2_sorted.tsv
sort demo/build/obi_3.tsv > demo/build/obi_3_sorted.tsv

# compare with original ontology 2

echo "#"
echo "# Comparing ontologies"
echo "#"

comm -3 demo/ldtab/obi_2_sorted.tsv demo/build/obi_2_sorted.tsv >> demo/diff_2.tsv
comm -3 demo/ldtab/obi_3_sorted.tsv demo/build/obi_3_sorted.tsv >> demo/diff_3.tsv


#head -n 1 demo/build/obi_2.tsv >> demo/build/obi_2_sorted.tsv
#tail -n +2 demo/build/obi_2.tsv | sort >> demo/build/obi_2_sorted.tsv
