#!/bin/bash

pg_dump --schema-only -h db-master.ipfire.org -U pakfire pakfire \
	> src/database.sql
