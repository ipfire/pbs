###############################################################################
#                                                                             #
# Pakfire - The IPFire package management system                              #
# Copyright (C) 2017 Pakfire development team                                 #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

ACLOCAL_AMFLAGS = -I m4 ${ACLOCAL_FLAGS}
AM_MAKEFLAGS = --no-print-directory
AUTOMAKE_OPTIONS = color-tests

# remove target it the command fails
.DELETE_ON_ERROR:

# keep itermediate files
.SECONDARY:

SUBDIRS = . po

pythondir  = $(pyexecdir)/pakfire

configsdir = $(sysconfdir)/pakfire

BUILT_SOURCES =
CLEANFILES =
DISTCLEANFILES =
EXTRA_DIST =
INSTALL_DIRS =
noinst_DATA =

@INTLTOOL_POLICY_RULE@

.PHONY: update-po
update-po:
	$(MAKE) -C po update-po

DISTCHECK_CONFIGURE_FLAGS = \
	--with-systemdsystemunitdir=$$dc_install_base/$(systemdsystemunitdir)

# ------------------------------------------------------------------------------

AM_V_XSLT   = $(AM_V_XSLT_$(V))
AM_V_XSLT_  = $(AM_V_XSLT_$(AM_DEFAULT_VERBOSITY))
AM_V_XSLT_0 = @echo "  XSLT    " $@;

# ------------------------------------------------------------------------------

dist_doc_DATA = \
	COPYING \
	README

# ------------------------------------------------------------------------------

dist_bin_SCRIPTS = \
	src/scripts/pakfire-build-service \
	src/scripts/pakfire-hub \
	src/scripts/pakfire-web

dist_configs_DATA = \
	pbs.conf.sample

buildservice_PYTHON = \
	src/buildservice/__init__.py \
	src/buildservice/__version__.py \
	src/buildservice/arches.py \
	src/buildservice/base.py \
	src/buildservice/bugtracker.py \
	src/buildservice/builders.py \
	src/buildservice/builds.py \
	src/buildservice/cache.py \
	src/buildservice/constants.py \
	src/buildservice/database.py \
	src/buildservice/decorators.py \
	src/buildservice/distribution.py \
	src/buildservice/geoip.py \
	src/buildservice/git.py \
	src/buildservice/jobqueue.py \
	src/buildservice/jobs.py \
	src/buildservice/keys.py \
	src/buildservice/ldap.py \
	src/buildservice/logs.py \
	src/buildservice/messages.py \
	src/buildservice/mirrors.py \
	src/buildservice/misc.py \
	src/buildservice/packages.py \
	src/buildservice/repository.py \
	src/buildservice/sessions.py \
	src/buildservice/settings.py \
	src/buildservice/sources.py \
	src/buildservice/updates.py \
	src/buildservice/uploads.py \
	src/buildservice/users.py

buildservicedir = $(pythondir)/buildservice

BUILT_SOURCES += \
	src/buildservice/constants.py

EXTRA_DIST += \
	src/buildservice/constants.py.in

CLEANFILES += \
	src/buildservice/constants.py

hub_PYTHON = \
	src/hub/__init__.py \
	src/hub/handlers.py

hubdir = $(buildservicedir)/hub

web_PYTHON = \
	src/web/__init__.py \
	src/web/api.py \
	src/web/auth.py \
	src/web/base.py \
	src/web/builders.py \
	src/web/builds.py \
	src/web/distributions.py \
	src/web/errors.py \
	src/web/handlers.py \
	src/web/handlers_jobs.py \
	src/web/handlers_keys.py \
	src/web/handlers_packages.py \
	src/web/handlers_search.py \
	src/web/handlers_updates.py \
	src/web/handlers_users.py \
	src/web/mirrors.py \
	src/web/ui_modules.py

webdir = $(buildservicedir)/web

# ------------------------------------------------------------------------------

dist_templates_DATA = \
	src/templates/base-form1.html \
	src/templates/base-form2.html \
	src/templates/base.html \
	src/templates/build-bugs.html \
	src/templates/build-delete.html \
	src/templates/build-detail.html \
	src/templates/build-filter.html \
	src/templates/build-index.html \
	src/templates/build-list.html \
	src/templates/build-manage.html \
	src/templates/build-priority.html \
	src/templates/build-queue.html \
	src/templates/build-schedule-test.html \
	src/templates/build-state.html \
	src/templates/builds-watchers-add.html \
	src/templates/builds-watchers-list.html \
	src/templates/distro-detail.html \
	src/templates/distro-edit.html \
	src/templates/distro-list.html \
	src/templates/distro-source-commit-detail.html \
	src/templates/distro-source-commit-reset.html \
	src/templates/distro-source-commits.html \
	src/templates/distro-source-detail.html \
	src/templates/distro-update-detail.html \
	src/templates/distro-update-edit.html \
	src/templates/docs-base.html \
	src/templates/docs-build.html \
	src/templates/docs-index.html \
	src/templates/docs-users.html \
	src/templates/docs-whatsthis.html \
	src/templates/file-detail.html \
	src/templates/index.html \
	src/templates/jobs-abort.html \
	src/templates/jobs-buildroot.html \
	src/templates/job-schedule-rebuild.html \
	src/templates/job-schedule-test.html \
	src/templates/jobs-detail.html \
	src/templates/jobs-filter.html \
	src/templates/jobs-index.html \
	src/templates/keys-delete.html \
	src/templates/keys-import.html \
	src/templates/keys-list.html \
	src/templates/log.html \
	src/templates/login.html \
	src/templates/package-detail.html \
	src/templates/package-detail-list.html \
	src/templates/package-properties.html \
	src/templates/packages-list.html \
	src/templates/register-activation-fail.html \
	src/templates/register-activation-success.html \
	src/templates/register-fail.html \
	src/templates/register.html \
	src/templates/register-success.html \
	src/templates/repository-detail.html \
	src/templates/repository-edit.html \
	src/templates/search-form.html \
	src/templates/search-results.html \
	src/templates/source-list.html \
	src/templates/updates-index.html \
	src/templates/uploads-list.html \
	src/templates/user-comments.html \
	src/templates/user-delete.html \
	src/templates/user-forgot-password.html \
	src/templates/user-impersonation.html \
	src/templates/user-list.html \
	src/templates/user-profile-builds.html \
	src/templates/user-profile-edit-fail.html \
	src/templates/user-profile-edit.html \
	src/templates/user-profile.html \
	src/templates/user-profile-need-activation.html \
	src/templates/user-profile-passwd.html \
	src/templates/user-profile-passwd-ok.html

templatesdir = $(datadir)/templates

dist_templates_builders_DATA = \
	src/templates/builders/delete.html \
	src/templates/builders/detail.html \
	src/templates/builders/edit.html \
	src/templates/builders/list.html \
	src/templates/builders/new.html \
	src/templates/builders/pass.html

templates_buildersdir = $(templatesdir)/builders

dist_templates_builds_DATA = \
	src/templates/builds/comments.html

templates_buildsdir = $(templatesdir)/builds

dist_templates_errors_DATA = \
	src/templates/errors/error.html \
	src/templates/errors/error-400.html \
	src/templates/errors/error-403.html \
	src/templates/errors/error-404.html

templates_errorsdir = $(templatesdir)/errors

dist_templates_mirrors_DATA = \
	src/templates/mirrors/delete.html \
	src/templates/mirrors/detail.html \
	src/templates/mirrors/edit.html \
	src/templates/mirrors/list.html \
	src/templates/mirrors/new.html

templates_mirrorsdir = $(templatesdir)/mirrors

dist_templates_modules_DATA = \
	src/templates/modules/bugs-table.html \
	src/templates/modules/build-headline.html \
	src/templates/modules/build-log.html \
	src/templates/modules/build-offset.html \
	src/templates/modules/build-state-warnings.html \
	src/templates/modules/build-table.html \
	src/templates/modules/comments-table.html \
	src/templates/modules/commits-table.html \
	src/templates/modules/files-table.html \
	src/templates/modules/footer.html \
	src/templates/modules/jobs-table.html \
	src/templates/modules/log-entry-comment.html \
	src/templates/modules/log-entry.html \
	src/templates/modules/log-entry-small.html \
	src/templates/modules/log-files-table.html \
	src/templates/modules/log.html \
	src/templates/modules/log-table.html \
	src/templates/modules/maintainer.html \
	src/templates/modules/modal-base.html \
	src/templates/modules/modal-build-comment.html \
	src/templates/modules/modal-build-push.html \
	src/templates/modules/modal-build-unpush.html \
	src/templates/modules/package-header.html \
	src/templates/modules/packages-files-table.html \
	src/templates/modules/packages-table.html \
	src/templates/modules/package-table-detail.html \
	src/templates/modules/repo-actions-table.html \
	src/templates/modules/repository-table.html \
	src/templates/modules/source-table.html \
	src/templates/modules/updates-table.html \
	src/templates/modules/user-table.html \
	src/templates/modules/watchers-sidebar-table.html

templates_modulesdir = $(templatesdir)/modules

dist_templates_modules_changelog_DATA = \
	src/templates/modules/changelog/entry.html \
	src/templates/modules/changelog/index.html

templates_modules_changelogdir = $(templates_modulesdir)/changelog

dist_templates_modules_jobs_DATA = \
	src/templates/modules/jobs/boxes.html \
	src/templates/modules/jobs/list.html \
	src/templates/modules/jobs/status.html

templates_modules_jobsdir = $(templates_modulesdir)/jobs

dist_templates_modules_packages_DATA = \
	src/templates/modules/packages/dependency-table.html

templates_modules_packagesdir = $(templates_modulesdir)/packages

dist_templates_modules_select_DATA = \
	src/templates/modules/select/locale.html \
	src/templates/modules/select/timezone.html

templates_modules_selectdir = $(templates_modulesdir)/select

dist_templates_packages_DATA = \
	src/templates/packages/changelog.html \
	src/templates/packages/view-file.html

templates_packagesdir = $(templatesdir)/packages

dist_templates_packages_builds_DATA = \
	src/templates/packages/builds/scratch.html \
	src/templates/packages/builds/times.html

templates_packages_buildsdir = $(templates_packagesdir)/builds

dist_templates_sessions_DATA = \
	src/templates/sessions/index.html

templates_sessionsdir = $(templatesdir)/sessions

# ------------------------------------------------------------------------------
#
dist_static_DATA = \
	src/static/favicon.ico \
	src/static/robots.txt

staticdir = $(datadir)/static

dist_static_css_DATA = \
	src/static/css/bootstrap-responsive.min.css \
	src/static/css/bootstrap.min.css \
	src/static/css/build-table.css \
	src/static/css/commits-table.css \
	src/static/css/font-awesome.css \
	src/static/css/jobs-list.css \
	src/static/css/jobs-table.css \
	src/static/css/log.css \
	src/static/css/packages-files-table.css \
	src/static/css/packages-table.css \
	src/static/css/prettify.css \
	src/static/css/style.css \
	src/static/css/watchers-sidebar-table.css

static_cssdir = $(staticdir)/css

dist_static_font_DATA = \
	src/static/font/fontawesome-webfont.eot \
	src/static/font/fontawesome-webfont.svg \
	src/static/font/fontawesome-webfont.ttf \
	src/static/font/fontawesome-webfont.woff

static_fontdir = $(staticdir)/font

dist_static_images_DATA = \
	src/static/images/icons/build-dependency_error.png \
	src/static/images/icons/build-dispatching.png \
	src/static/images/icons/build-failed.png \
	src/static/images/icons/build-finished.png \
	src/static/images/icons/build-pending.png \
	src/static/images/icons/build-running.png \
	src/static/images/icons/build-unknown.png \
	src/static/images/icons/build-uploading.png \
	src/static/images/icons/build-waiting.png \
	src/static/images/icons/builder-disabled.png \
	src/static/images/img01.jpg \
	src/static/images/img02.jpg \
	src/static/images/img03.jpg \
	src/static/images/img04.jpg \
	src/static/images/ipfire_tux_128x128.png \
	src/static/images/readme.txt

static_imagesdir = $(staticdir)/images

dist_static_js_DATA = \
	src/static/js/bootstrap.min.js \
	src/static/js/jquery.js \
	src/static/js/pbs.js \
	src/static/js/prettify.js

static_jsdir = $(staticdir)/js

# ------------------------------------------------------------------------------

EXTRA_DIST += \
	Dockerfile.in

docker_DATA = \
	Dockerfile

CLEANFILES += \
	Dockerfile

dockerdir = $(datadir)/docker

.PHONY: docker
docker: Dockerfile
	docker build -t "ipfire/pakfire-build-service:$(PACKAGE_VERSION)" .

# ------------------------------------------------------------------------------

if HAVE_SYSTEMD
systemdsystemunit_DATA = \
	# TODO

CLEANFILES += \
	 $(systemdsystemunit_DATA)

INSTALL_DIRS += \
	$(systemdsystemunitdir)
endif

EXTRA_DIST += \
	# TODO

dist_database_DATA = \
	src/database.sql

databasedir = $(datadir)/database

dist_cron_DATA = \
	src/crontab/pakfire-build-service

crondir = $(sysconfdir)/cron.d

dist_geoip_DATA = \
	src/geoip/GeoLite2-Country.mmdb

geoipdir = $(datadir)/geoip

EXTRA_DIST += \
	src/tools/dump-database-schema.sh \
	src/tools/update-geoip-database.sh

# ------------------------------------------------------------------------------

substitutions = \
	'|PACKAGE_NAME=$(PACKAGE_NAME)|' \
	'|PACKAGE_VERSION=$(PACKAGE_VERSION)|' \
	'|configsdir=$(configsdir)|' \
	'|bindir=$(bindir)|' \
	'|datadir=$(datadir)|' \
	'|localedir=$(localedir)|' \
	'|templatesdir=$(templatesdir)|' \
	'|staticdir=$(staticdir)|'

SED_PROCESS = \
	$(AM_V_GEN)$(MKDIR_P) $(dir $@) && \
	$(SED) $(subst '|,-e 's|@,$(subst =,\@|,$(subst |',|g',$(substitutions)))) \
		< $< > $@

%: %.in Makefile
	$(SED_PROCESS)
