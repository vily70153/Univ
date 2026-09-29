#!/bin/sh

echo "Building library was start..."


c++ -c -Idir/ src/subtract.cpp	-o build/subtract.o
c++ -c -Idir/ src/sum.cpp	-o build/sum.o

ar rcs build/libipb_arithmetic.a build/sum.o build/subtract.o

c++ -std=c++17 -Iinclude/ src/main.cpp -o main -Lbuild/ -lipb_arithmetic

mv main results/bin/
