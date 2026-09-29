#!/bin/sh

mkdir -p ./install/bin
mkdir -p ./install/lib
mkdir -p ./install/include

cp ./results/bin/main ./install/bin/

cp ./build/libipb_arithmetic.a ./install/lib/

cp -r ./include/* ./install/include/