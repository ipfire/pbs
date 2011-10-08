#!/usr/bin/python

N_ = lambda x: x

# NEVER EVER CHANGE ONE OF THE IDS!
LOG_BUILD_CREATED				= 1
LOG_BUILD_STATE_PENDING			= 2
LOG_BUILD_STATE_DISPATCHING		= 3
LOG_BUILD_STATE_RUNNING			= 4
LOG_BUILD_STATE_FAILED			= 5
LOG_BUILD_STATE_PERM_FAILED		= 6
LOG_BUILD_STATE_DEP_ERROR		= 7
LOG_BUILD_STATE_WAITING			= 8
LOG_BUILD_STATE_FINISHED		= 9
LOG_BUILD_STATE_UNKNOWN			= 10
LOG_BUILD_STATE_UPLOADING		= 11

LOG_PKG_CREATED					= 20


LOG2MSG = {
	LOG_BUILD_CREATED			: N_("Build job created"),
	LOG_BUILD_STATE_PENDING		: N_("Build job is now pending"),
	LOG_BUILD_STATE_DISPATCHING	: N_("Build job is dispatching"),
	LOG_BUILD_STATE_RUNNING		: N_("Build job is running"),
	LOG_BUILD_STATE_FAILED		: N_("Build job has failed"),
	LOG_BUILD_STATE_PERM_FAILED	: N_("Build job has permanently failed"),
	LOG_BUILD_STATE_DEP_ERROR	: N_("Build job has dependency errors"),
	LOG_BUILD_STATE_WAITING		: N_("Build job is waiting for the source package"),
	LOG_BUILD_STATE_FINISHED	: N_("Build job is finished"),
	LOG_BUILD_STATE_UNKNOWN		: N_("Build job has an unknown state"),
	LOG_BUILD_STATE_UPLOADING	: N_("Build job is uploading"),
}

UPLOADS_DIR = "/var/tmp/pakfire/uploads"

MSG_BUILD_FAILED_SUBJECT = N_("[%(build_name)s] Build job failed.")
MSG_BUILD_FAILED = N_("""\
The build job "%(build_name)s" has failed.

This could have a couple of reasons and needs to be investigated by you.

Here is more information about the incident:

    Build name: %(build_name)s
    Build host: %(build_host)s

Click on this link to get all details about the build:
    http://pakfire.ipfire.org/build/%(build_uuid)s

Sincerely,
    The Pakfire Build Service""")


MSG_BUILD_FINISHED_SUBJECT = N_("[%(build_name)s] Build job finished.")
MSG_BUILD_FINISHED = N_("""\
The build job "%(build_name)s" has finished.

If you are the maintainer, it is up to you to push it to one or more repositories.

Click on this link to get all details about the build:
    http://pakfire.ipfire.org/build/%(build_uuid)s

Sincerely,
    The Pakfire Build Service""")
