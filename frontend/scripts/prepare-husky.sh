#!/bin/sh

if [ ! -e ../.git ]; then
  exit 0
fi

cd .. && husky frontend/.husky
