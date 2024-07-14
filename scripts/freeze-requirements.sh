#!/bin/bash

# Paths to the requirement files
INITIAL_FILE="requirements.txt"
REQS_FILE="requirements-req.txt"
FINAL_FILE="requirements-final.txt"

# cp $REQUIREMENTS_FILE "initial-$REQUIREMENTS_FILE"

# Generate requirements.txt using pipreqs
pipreqs . --force --savepath $REQS_FILE &> /dev/null

# Combine the two files and remove duplicates
cat $REQS_FILE $INITIAL_FILE | sort -u > $FINAL_FILE

# Remove pipreq requirement file
rm $INITIAL_FILE
rm $REQS_FILE
mv $FINAL_FILE $INITIAL_FILE

# Print success message
echo -e "\e[32mRequirement.txt generated\e[0m"

