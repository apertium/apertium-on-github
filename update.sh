#!/bin/sh

git submodule update --recursive --remote
git commit -a -m "Update submodules"
git push
