#!/usr/bin/env bash

today=`date +%Y-%m-%d`
yesterday=`date -d "yesterday" +%Y-%m-%d`

function logger(){
    echo `date "+%Y-%m-%d %H:%M:%S"` $1
}