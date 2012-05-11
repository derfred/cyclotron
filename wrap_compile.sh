#!/bin/sh
ulimit -m 10000000

case $1 in
  python)
    /usr/nld/python-2.7.2/bin/python ${@:2}
    ;;
  sage)
    /usr/nld/sage-4.8-fat-x86_64-Linux/sage -python ${@:2}
    ;;
esac
