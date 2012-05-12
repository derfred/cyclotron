#!/bin/sh

find $1 -type f -wholename "*stderrs*" ! -size 0
