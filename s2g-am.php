#!/usr/bin/env php
<?php

$meta = shell_exec('head -n3 '.escapeshellarg($argv[1]).' | tail -n2');
if (preg_match('~From: (.+?) <([^<>]+)>\nDate: ([^\n]+)~', $meta, $m)) {
	putenv('GIT_COMMITTER_NAME='.$m[1]);
	putenv('GIT_COMMITTER_EMAIL='.$m[2]);
	putenv('GIT_COMMITTER_DATE='.$m[3]);
	echo shell_exec('git am -k --ignore-whitespace '.escapeshellarg($argv[1]).' 2>&1');
}
