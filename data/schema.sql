-- phpMyAdmin SQL Dump
-- version 3.5.4
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Feb 17, 2013 at 03:01 PM
-- Server version: 5.1.67-log
-- PHP Version: 5.3.3

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `pakfire`
--

-- --------------------------------------------------------

--
-- Table structure for table `arches`
--

CREATE TABLE IF NOT EXISTS `arches` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `prio` int(11) NOT NULL DEFAULT '0',
  `binary` enum('Y','N') NOT NULL DEFAULT 'Y',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builders`
--

CREATE TABLE IF NOT EXISTS `builders` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `passphrase` varchar(255) DEFAULT NULL,
  `description` text,
  `status` enum('enabled','disabled','deleted') NOT NULL DEFAULT 'disabled',
  `disabled` enum('Y','N') NOT NULL DEFAULT 'Y',
  `loadavg` varchar(32) NOT NULL DEFAULT '0',
  `arches` varchar(128) DEFAULT NULL,
  `build_release` enum('Y','N') NOT NULL DEFAULT 'N',
  `build_scratch` enum('Y','N') NOT NULL DEFAULT 'N',
  `build_test` enum('Y','N') NOT NULL DEFAULT 'N',
  `max_jobs` int(11) NOT NULL DEFAULT '1',
  `pakfire_version` varchar(32) DEFAULT NULL,
  `cpu_model` varchar(255) DEFAULT NULL,
  `cpu_count` tinyint(4) NOT NULL DEFAULT '1',
  `memory` bigint(20) unsigned NOT NULL DEFAULT '0',
  `overload` enum('Y','N') NOT NULL DEFAULT 'N',
  `free_space` int(11) NOT NULL DEFAULT '0',
  `host_key_id` varchar(64) DEFAULT NULL,
  `deleted` enum('Y','N') NOT NULL DEFAULT 'N',
  `time_created` datetime NOT NULL,
  `time_updated` datetime DEFAULT NULL,
  `time_keepalive` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builders_arches`
--

CREATE TABLE IF NOT EXISTS `builders_arches` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `builder_id` int(11) unsigned NOT NULL,
  `arch_id` int(11) unsigned NOT NULL,
  `enabled` enum('Y','N') NOT NULL DEFAULT 'Y',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builders_history`
--

CREATE TABLE IF NOT EXISTS `builders_history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `builder_id` int(10) unsigned NOT NULL,
  `action` enum('created','enabled','disabled','deleted') NOT NULL,
  `user_id` int(10) unsigned DEFAULT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builds`
--

CREATE TABLE IF NOT EXISTS `builds` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `uuid` varchar(40) NOT NULL,
  `pkg_id` int(11) unsigned NOT NULL,
  `type` enum('release','scratch') NOT NULL DEFAULT 'release',
  `state` enum('building','testing','stable','obsolete','broken') NOT NULL DEFAULT 'building',
  `severity` enum('security update','bugfix update','enhancement','new package') DEFAULT NULL,
  `message` text,
  `time_created` datetime NOT NULL,
  `update_year` int(11) DEFAULT NULL,
  `update_num` int(11) DEFAULT NULL,
  `depends_on` int(11) unsigned DEFAULT NULL,
  `distro_id` int(11) NOT NULL,
  `owner_id` int(11) unsigned DEFAULT NULL,
  `public` enum('Y','N') NOT NULL DEFAULT 'Y',
  `priority` int(11) NOT NULL DEFAULT '0',
  `auto_move` enum('N','Y') NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builds_bugs`
--

CREATE TABLE IF NOT EXISTS `builds_bugs` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `build_id` int(10) unsigned NOT NULL,
  `bug_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `build_id` (`build_id`,`bug_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builds_bugs_updates`
--

CREATE TABLE IF NOT EXISTS `builds_bugs_updates` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `bug_id` int(10) unsigned NOT NULL,
  `status` varchar(32) DEFAULT NULL,
  `resolution` varchar(32) DEFAULT NULL,
  `comment` text,
  `time` datetime NOT NULL,
  `error` enum('N','Y') NOT NULL DEFAULT 'N',
  `error_msg` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builds_comments`
--

CREATE TABLE IF NOT EXISTS `builds_comments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `build_id` int(10) unsigned NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  `text` text NOT NULL,
  `credit` tinyint(4) NOT NULL,
  `time_created` datetime NOT NULL,
  `time_updated` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `builds_history`
--

CREATE TABLE IF NOT EXISTS `builds_history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `build_id` int(10) unsigned NOT NULL,
  `action` enum('created','bug_added','bug_removed') NOT NULL,
  `user_id` int(10) unsigned DEFAULT NULL,
  `time` datetime NOT NULL,
  `bug_id` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Stand-in structure for view `builds_latest`
--
CREATE TABLE IF NOT EXISTS `builds_latest` (
`build_id` int(10) unsigned
,`build_type` enum('release','scratch')
,`build_state` enum('building','testing','stable','obsolete','broken')
,`package_name` varchar(128)
,`public` enum('Y','N')
);
-- --------------------------------------------------------

--
-- Stand-in structure for view `builds_times`
--
CREATE TABLE IF NOT EXISTS `builds_times` (
`build_id` int(10) unsigned
,`arch` varchar(32)
,`job_type` enum('build','test')
,`duration` bigint(11)
);
-- --------------------------------------------------------

--
-- Table structure for table `builds_watchers`
--

CREATE TABLE IF NOT EXISTS `builds_watchers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `build_id` int(10) unsigned NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `distributions`
--

CREATE TABLE IF NOT EXISTS `distributions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `sname` varchar(64) NOT NULL,
  `slogan` varchar(255) NOT NULL,
  `description` text,
  `vendor` varchar(64) NOT NULL,
  `contact` varchar(128) DEFAULT NULL,
  `tag` varchar(4) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `distro_arches`
--

CREATE TABLE IF NOT EXISTS `distro_arches` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `distro_id` int(10) unsigned NOT NULL,
  `arch_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `filelists`
--

CREATE TABLE IF NOT EXISTS `filelists` (
  `pkg_id` int(10) unsigned NOT NULL,
  `name` varchar(1024) NOT NULL,
  `size` int(11) NOT NULL,
  `hash_sha512` varchar(140) DEFAULT NULL,
  `type` tinyint(4) NOT NULL,
  `config` enum('Y','N') NOT NULL,
  `mode` int(11) NOT NULL,
  `user` varchar(32) NOT NULL,
  `group` varchar(32) NOT NULL,
  `mtime` datetime NOT NULL,
  `capabilities` varchar(64) DEFAULT NULL,
  KEY `pkg_id` (`pkg_id`),
  KEY `name` (`name`(8))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `jobs`
--

CREATE TABLE IF NOT EXISTS `jobs` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `uuid` varchar(40) NOT NULL,
  `type` enum('build','test') NOT NULL DEFAULT 'build',
  `build_id` int(11) unsigned NOT NULL,
  `state` enum('new','pending','running','finished','dispatching','uploading','failed','aborted','temporary_failed','dependency_error','aborted','download_error','deleted') NOT NULL DEFAULT 'new',
  `arch_id` int(11) unsigned NOT NULL,
  `time_created` datetime NOT NULL,
  `time_started` datetime DEFAULT NULL,
  `time_finished` datetime DEFAULT NULL,
  `start_not_before` datetime DEFAULT NULL,
  `builder_id` int(11) unsigned DEFAULT NULL,
  `tries` int(11) unsigned NOT NULL DEFAULT '0',
  `aborted_state` smallint(6) NOT NULL DEFAULT '0',
  `message` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `jobs_buildroots`
--

CREATE TABLE IF NOT EXISTS `jobs_buildroots` (
  `job_id` int(10) unsigned NOT NULL,
  `tries` tinyint(3) unsigned NOT NULL,
  `pkg_uuid` varchar(40) NOT NULL,
  `pkg_name` varchar(1024) NOT NULL,
  KEY `job_id` (`job_id`),
  KEY `pkg_uuid` (`pkg_uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `jobs_history`
--

CREATE TABLE IF NOT EXISTS `jobs_history` (
  `job_id` int(10) unsigned NOT NULL,
  `action` enum('created','state_change','reset','schedule_rebuild','schedule_test_job') NOT NULL,
  `state` enum('new','pending','running','finished','dispatching','uploading','failed','temporary_failed','dependency_error','aborted','download_error','deleted') DEFAULT NULL,
  `user_id` int(10) unsigned DEFAULT NULL,
  `time` datetime NOT NULL,
  `builder_id` int(11) DEFAULT NULL,
  `test_job_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `jobs_packages`
--

CREATE TABLE IF NOT EXISTS `jobs_packages` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `job_id` int(10) unsigned NOT NULL,
  `pkg_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `jobs_repos`
--

CREATE TABLE IF NOT EXISTS `jobs_repos` (
  `job_id` int(10) unsigned NOT NULL,
  `repo_id` int(10) unsigned NOT NULL,
  UNIQUE KEY `job_id` (`job_id`,`repo_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `keys`
--

CREATE TABLE IF NOT EXISTS `keys` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fingerprint` varchar(64) NOT NULL,
  `uids` varchar(255) NOT NULL,
  `data` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `fingerprint` (`fingerprint`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `keys_subkeys`
--

CREATE TABLE IF NOT EXISTS `keys_subkeys` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `key_id` int(10) unsigned NOT NULL,
  `fingerprint` varchar(64) NOT NULL,
  `time_created` datetime NOT NULL,
  `time_expires` datetime DEFAULT NULL,
  `algo` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `logfiles`
--

CREATE TABLE IF NOT EXISTS `logfiles` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `job_id` int(10) unsigned NOT NULL,
  `path` varchar(255) NOT NULL,
  `filesize` int(10) unsigned NOT NULL,
  `hash_sha512` varchar(140) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `mirrors`
--

CREATE TABLE IF NOT EXISTS `mirrors` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `hostname` varchar(128) NOT NULL,
  `path` varchar(128) NOT NULL,
  `owner` varchar(128) DEFAULT NULL,
  `contact` varchar(128) DEFAULT NULL,
  `status` enum('enabled','disabled','deleted') NOT NULL DEFAULT 'disabled',
  `check_status` enum('UNKNOWN','UP','DOWN') NOT NULL DEFAULT 'UNKNOWN',
  `last_check` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `mirrors_history`
--

CREATE TABLE IF NOT EXISTS `mirrors_history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mirror_id` int(10) unsigned NOT NULL,
  `action` enum('created','enabled','disabled','deleted') NOT NULL,
  `user_id` int(10) unsigned DEFAULT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `packages`
--

CREATE TABLE IF NOT EXISTS `packages` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `epoch` int(11) unsigned NOT NULL,
  `version` varchar(128) NOT NULL,
  `release` varchar(32) NOT NULL,
  `type` enum('source','binary') NOT NULL,
  `arch` tinyint(3) unsigned NOT NULL,
  `groups` varchar(1024) NOT NULL,
  `maintainer` varchar(128) NOT NULL,
  `license` varchar(128) NOT NULL,
  `url` varchar(1024) NOT NULL,
  `summary` text NOT NULL,
  `description` text NOT NULL,
  `size` int(10) unsigned NOT NULL,
  `supported_arches` varchar(64) DEFAULT NULL,
  `uuid` varchar(40) NOT NULL,
  `commit_id` int(10) unsigned DEFAULT NULL,
  `build_id` varchar(40) NOT NULL,
  `build_host` varchar(128) NOT NULL,
  `build_time` datetime NOT NULL,
  `path` varchar(255) NOT NULL,
  `filesize` int(10) unsigned NOT NULL,
  `hash_sha512` varchar(140) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `uuid` (`uuid`),
  FULLTEXT KEY `search` (`name`,`summary`,`description`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `packages_deps`
--

CREATE TABLE IF NOT EXISTS `packages_deps` (
  `pkg_id` int(10) unsigned NOT NULL,
  `type` enum('requires','prerequires','provides','conflicts','obsoletes','suggests','recommends') NOT NULL,
  `what` varchar(1024) NOT NULL,
  KEY `pkg_id` (`pkg_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `packages_properties`
--

CREATE TABLE IF NOT EXISTS `packages_properties` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `critical_path` enum('N','Y') NOT NULL DEFAULT 'N',
  `priority` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `queue_delete`
--

CREATE TABLE IF NOT EXISTS `queue_delete` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `path` varchar(1024) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `repositories`
--

CREATE TABLE IF NOT EXISTS `repositories` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `type` enum('testing','unstable','stable') NOT NULL DEFAULT 'testing',
  `description` text NOT NULL,
  `distro_id` int(10) unsigned NOT NULL,
  `parent_id` int(10) unsigned DEFAULT NULL,
  `key_id` int(10) unsigned DEFAULT NULL,
  `mirrored` enum('N','Y') NOT NULL DEFAULT 'N',
  `enabled_for_builds` enum('N','Y') NOT NULL DEFAULT 'N',
  `score_needed` int(10) unsigned NOT NULL DEFAULT '0',
  `last_update` datetime DEFAULT NULL,
  `time_min` int(10) unsigned NOT NULL DEFAULT '0',
  `time_max` int(10) unsigned NOT NULL DEFAULT '0',
  `update_started` datetime DEFAULT NULL,
  `update_ended` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `repositories_aux`
--

CREATE TABLE IF NOT EXISTS `repositories_aux` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `description` text,
  `url` varchar(128) NOT NULL,
  `distro_id` int(10) unsigned NOT NULL,
  `status` enum('enabled','disabled') NOT NULL DEFAULT 'disabled',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `repositories_builds`
--

CREATE TABLE IF NOT EXISTS `repositories_builds` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `repo_id` int(10) unsigned NOT NULL,
  `build_id` int(10) unsigned NOT NULL,
  `time_added` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `build_id` (`build_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `repositories_history`
--

CREATE TABLE IF NOT EXISTS `repositories_history` (
  `build_id` int(10) unsigned NOT NULL,
  `action` enum('added','removed','moved') NOT NULL,
  `from_repo_id` int(10) unsigned DEFAULT NULL,
  `to_repo_id` int(10) unsigned DEFAULT NULL,
  `user_id` int(10) unsigned DEFAULT NULL,
  `time` datetime NOT NULL,
  KEY `build_id` (`build_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `sessions`
--

CREATE TABLE IF NOT EXISTS `sessions` (
  `session_id` varchar(64) NOT NULL,
  `user_id` int(11) NOT NULL,
  `impersonated_user_id` int(10) unsigned DEFAULT NULL,
  `creation_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `valid_until` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `from_address` varchar(255) DEFAULT NULL,
  UNIQUE KEY `session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `settings`
--

CREATE TABLE IF NOT EXISTS `settings` (
  `k` varchar(255) NOT NULL,
  `v` varchar(1024) NOT NULL,
  UNIQUE KEY `k` (`k`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `slogans`
--

CREATE TABLE IF NOT EXISTS `slogans` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `message` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `sources`
--

CREATE TABLE IF NOT EXISTS `sources` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `identifier` varchar(128) NOT NULL,
  `url` varchar(1024) NOT NULL,
  `gitweb` varchar(255) DEFAULT NULL,
  `revision` varchar(40) NOT NULL,
  `branch` varchar(32) NOT NULL,
  `updated` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP,
  `distro_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `identifier` (`identifier`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `sources_commits`
--

CREATE TABLE IF NOT EXISTS `sources_commits` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `source_id` int(10) unsigned NOT NULL,
  `revision` varchar(40) NOT NULL,
  `author` varchar(1024) NOT NULL,
  `committer` varchar(1024) NOT NULL,
  `subject` varchar(1024) NOT NULL,
  `body` text NOT NULL,
  `date` datetime NOT NULL,
  `state` enum('pending','running','finished','failed') NOT NULL DEFAULT 'pending',
  PRIMARY KEY (`id`),
  KEY `revision` (`revision`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `uploads`
--

CREATE TABLE IF NOT EXISTS `uploads` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `uuid` varchar(40) NOT NULL,
  `user_id` int(10) unsigned DEFAULT NULL,
  `builder_id` int(11) unsigned DEFAULT NULL,
  `filename` varchar(1024) NOT NULL,
  `hash` varchar(40) NOT NULL,
  `size` int(11) NOT NULL,
  `progress` int(11) NOT NULL DEFAULT '0',
  `finished` enum('N','Y') NOT NULL DEFAULT 'N',
  `time_started` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `time_finished` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `realname` varchar(255) DEFAULT NULL,
  `passphrase` varchar(153) NOT NULL,
  `state` enum('user','tester','admin') NOT NULL,
  `locale` varchar(8) DEFAULT NULL,
  `timezone` varchar(64) DEFAULT NULL,
  `activated` enum('Y','N') NOT NULL DEFAULT 'N',
  `activation_code` varchar(20) DEFAULT NULL,
  `deleted` enum('Y','N') NOT NULL DEFAULT 'N',
  `registered` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  FULLTEXT KEY `search` (`name`,`realname`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users_emails`
--

CREATE TABLE IF NOT EXISTS `users_emails` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `email` varchar(128) NOT NULL,
  `primary` enum('N','Y') NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users_permissions`
--

CREATE TABLE IF NOT EXISTS `users_permissions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `create_scratch_builds` enum('Y','N') NOT NULL DEFAULT 'N',
  `maintain_builders` enum('N','Y') NOT NULL DEFAULT 'N',
  `manage_critical_path` enum('N','Y') NOT NULL DEFAULT 'N',
  `manage_mirrors` enum('N','Y') NOT NULL DEFAULT 'N',
  `vote` enum('N','Y') NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user_messages`
--

CREATE TABLE IF NOT EXISTS `user_messages` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `frm` varchar(255) NOT NULL,
  `to` varchar(2048) NOT NULL,
  `subject` varchar(1024) NOT NULL,
  `text` text NOT NULL,
  `time_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure for view `builds_latest`
--
DROP TABLE IF EXISTS `builds_latest`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `builds_latest` AS select `builds`.`id` AS `build_id`,`builds`.`type` AS `build_type`,`builds`.`state` AS `build_state`,`packages`.`name` AS `package_name`,`builds`.`public` AS `public` from (`builds` left join `packages` on((`builds`.`pkg_id` = `packages`.`id`))) where (`builds`.`id` in (select `repositories_builds`.`build_id` from `repositories_builds`) or ((`builds`.`time_created` >= (select `builds`.`time_created` from ((`builds` left join `repositories_builds` on((`builds`.`id` = `repositories_builds`.`build_id`))) left join `packages` `p` on((`builds`.`pkg_id` = `p`.`id`))) where (`p`.`name` = `packages`.`name`) order by `builds`.`time_created` limit 1)) and (`builds`.`state` not in ('obsolete','broken'))));

-- --------------------------------------------------------

--
-- Structure for view `builds_times`
--
DROP TABLE IF EXISTS `builds_times`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `builds_times` AS select `builds`.`id` AS `build_id`,`arches`.`name` AS `arch`,`jobs`.`type` AS `job_type`,(unix_timestamp(`jobs`.`time_finished`) - unix_timestamp(`jobs`.`time_started`)) AS `duration` from (((`jobs` left join `builds` on((`jobs`.`build_id` = `builds`.`id`))) left join `packages` on((`builds`.`pkg_id` = `packages`.`id`))) left join `arches` on((`jobs`.`arch_id` = `arches`.`id`))) where (`jobs`.`state` = 'finished');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
