#!/usr/bin/env php
<?php

$repo = 'file:///home/apertium/svn-mirror/apertium-sf-net';
$path = $argv[1];
$rev = $argv[2] ?? 'HEAD';

$log = shell_exec('svn log -v --xml -r'.$rev.':0 '.$repo.$path.'@'.$rev);
$xml = new DOMDocument;
$xml->loadXML($log);

$es = $xml->getElementsByTagName('logentry');

// <logentry  revision="3423"> <author>ftyers</author> <date>2008-01-19T16:03:22.122861Z</date> <paths> <path  prop-mods="false"  text-mods="false"  kind="dir"  action="D">/apertium-unicode</path> <path  prop-mods="false"  text-mods="false"  kind="dir"  action="D">/lttoolbox-unicode</path> <path  action="A"  prop-mods="false"  text-mods="false"  kind="dir"  copyfrom-path="/apertium-unicode"  copyfrom-rev="3416">/trunk/apertium-unicode</path> <path  text-mods="false"  kind="dir"  copyfrom-path="/lttoolbox-unicode"  copyfrom-rev="3422"  action="A"  prop-mods="false">/trunk/lttoolbox</path> </paths> <msg>Moving unicode apertium to trunk  </msg> </logentry>
foreach ($es as $e) {
	$rev = $e->getAttribute('revision');
	echo "$rev $path\n";

	$ps = $e->getElementsByTagName('path');
	foreach ($ps as $p) {
		if ($p->nodeValue === $path && $p->hasAttribute('copyfrom-path')) {
			$path = $p->getAttribute('copyfrom-path');
		}
	}
}
