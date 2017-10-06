#!/bin/bash

URL="http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.tar.gz"

tmpfile=$(mktemp)

# Download the file
if ! wget "${URL}" -O "${tmpfile}"; then
	echo "Could not download the database file" >&2
	unlink "${tmpfile}"

	exit 1
fi

# Extract database from tarball
if ! tar xvOf "${tmpfile}" "*/GeoLite2-Country.mmdb" > src/geoip/GeoLite2-Country.mmdb; then
	echo "Could not extract the database" >&2
	unlink "${tmpfile}"

	exit 1
fi

echo "OK"
exit 0
