#!/bin/bash
# 04-02-2020/SB
# creates a dump File for a specified PostgreSQL database
# should be executed periodically
# from a database user (f.e. postgres)
# the dump is archived/compressed and deleted afterwards

command=$(basename "$0")
# shows the basic functionality of the script
function fu_usage() {
    printf "\n\e[1;42m\tUsage:\e[0m \e[91m%s \e[34m<database> \e[92m<folder> \e[96m<days>\e[0m\n" "$command"
    printf "\n\t\t\e[34mdatabase:\e[0m specifies the name of the database\n"
    printf "\t\t\e[92mfolder:\e[0m specifies the folder where the dump should be stored\n"
    printf "\t\t\e[96mdays:\e[0m all dumps older will be deleted\n\n"
}

# checks if two parameters are set
if [[ $# -lt 3 ]]
then
    fu_usage
    exit 1
fi

# Variables
database="$1"
directory="$2"
dump="$directory/$(date +%d_%m).dump"
# specifies how long dumps should stay
days="$3"

# checks if the needed binaries exist
function fu_check_binaries() {
    for binary in "$@"
    do
	ret=$(which "$binary" 2> /dev/null)
	if [[ -n "$ret" && -x "$ret" ]]
	then
	    printf "\e[92m Binary \e[34m%s \e[92m exists!\e[0m\n" "$ret"
	else
	    printf "\t\e[1;91m Command \e[34m%s \e[91mnot found!\e[0m\n" "$binary" >&2
	    exit 1
	fi
    done
}


fu_check_binaries psql tar gzip

# checks if the database exists
# note the database "postgres" needs to exist
function fu_check_existance_of_database() {
    for db in postgres $database
    do 
	if psql -lt | cut -d \| -f 1 | sed 's/ //' | grep -qw "$db"
	then
	    printf "\e[92m Database \e[34m%s \e[92mexists!\e[0m\n" "$db"
	else
	    printf "\e[91m Database \e[34m%s \e[91mdoes not exist!\e[0m\n" "$db"
	    exit 1
	fi
    done
}

fu_check_existance_of_database

# check if the directory exists
function fu_check_existance_of_directory() {
    if [[ -d "$directory" ]]
    then
	printf "\e[92m The directory \e[34m%s \e[92mexists!\e[0m\n" "$directory"
    else
	printf "\e[91m The directory \e[34m%s \e[91mdoes not exist! Please choose another directory\e[0m\n" "$directory"
	exit 1
    fi
}

fu_check_existance_of_directory

# check if the directory is writable by the user
function fu_check_write_permissions_of_directory() {
    if [[ -w "$directory" ]]
    then
	printf "\e[92m The directory \e[34m%s \e[92mis writable!\e[0m\n" "$directory"
    else
	printf "\e[91m The directory \e[34m%s \e[91mis not writable! Please choose another directory\e[0m\n" "$directory"
	exit 1
    fi
}

fu_check_write_permissions_of_directory

function fu_create_dump() {
    pg_dump "$database" > "$dump"
}

fu_create_dump

# compresses the dump via gzip to save space
function fu_compress_dump() {
    tar czf "$dump".tar.gz "$dump"
}

fu_compress_dump

# deletes the original dump so that only the compressed one is being kept
function fu_delete_dump() {
    rm "$dump"
}

fu_delete_dump

# deletes old compressed dumps older than x days
function fu_delete_old_compressed_dumps() {
    find "$directory" -mtime +"$days" -delete;
}

fu_delete_old_compressed_dumps
