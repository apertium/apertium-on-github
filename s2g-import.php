#!/usr/bin/env php
<?php

$repo = 'file:///home/apertium/svn-mirror/apertium-sf-net';
$revs = explode("\n", trim(file_get_contents($argv[1])));
natsort($revs);

$s2g = [];
$s2gs = explode("\n", trim(file_get_contents($argv[2])));
foreach ($s2gs as $s) {
	if (preg_match('~^(\S+) = (.+?) <([^<>]+)>$~u', trim($s), $m)) {
		$s2g[$m[1]] = [$m[2], $m[3]];
	}
}

$uid = 's2g-'.bin2hex(random_bytes(8));
mkdir("/tmp/$uid");
chdir("/tmp/$uid");

mkdir('git');
chdir('git');
echo shell_exec('git init 2>&1');

// <logentry  revision="3423"> <author>ftyers</author> <date>2008-01-19T16:03:22.122861Z</date> <paths> <path  prop-mods="false"  text-mods="false"  kind="dir"  action="D">/apertium-unicode</path> <path  prop-mods="false"  text-mods="false"  kind="dir"  action="D">/lttoolbox-unicode</path> <path  action="A"  prop-mods="false"  text-mods="false"  kind="dir"  copyfrom-path="/apertium-unicode"  copyfrom-rev="3416">/trunk/apertium-unicode</path> <path  text-mods="false"  kind="dir"  copyfrom-path="/lttoolbox-unicode"  copyfrom-rev="3422"  action="A"  prop-mods="false">/trunk/lttoolbox</path> </paths> <msg>Moving unicode apertium to trunk  </msg> </logentry>
foreach ($revs as $rev) {
	chdir("/tmp/$uid");

	list($rev,$path) = explode(' ', $rev);

	$xml = new DOMDocument;
	$xml->loadXML(shell_exec('svn log -v --xml -r'.$rev.' '.$repo.$path.'@'.$rev));
	$author = $xml->getElementsByTagName('author')->item(0)->nodeValue;
	$date = $xml->getElementsByTagName('date')->item(0)->nodeValue;
	$msg = trim($xml->getElementsByTagName('msg')->item(0)->nodeValue);
	echo "$rev\t$author\t$date\t$msg\n";
	file_put_contents('msg', "{$msg}\n\ngit-svn-id: https://svn.code.sf.net/p/apertium/svn{$path}@{$rev} 72bbbca6-d526-0410-a7d9-f06f51895060");

	shell_exec('svn export --ignore-externals -r'.$rev.' '.$repo.$path.'/@'.$rev.' svn/');

	shell_exec('rsync -av --delete svn/ git/ --exclude=.git');
	shell_exec('rm -rf svn');

	chdir('git');
	echo shell_exec('git add . --all 2>&1');

	if (empty($s2g[$author])) {
		die("No such author $author!\n");
	}
	$author = $s2g[$author];
	putenv('GIT_COMMITTER_NAME='.$author[0]);
	putenv('GIT_COMMITTER_EMAIL='.$author[1]);
	putenv('GIT_COMMITTER_DATE='.$date);

	echo shell_exec("git commit -F ../msg --allow-empty --author ".escapeshellarg("{$author[0]} <{$author[1]}>")." --date '{$date}' 2>&1");

	echo "\n";
}

chdir('/tmp/');
//shell_exec("rm -rf '$uid'");
