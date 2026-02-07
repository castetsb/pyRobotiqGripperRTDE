#!/bin/bash

set -e  # stop on first error

PACKAGES=(
  pyserial-2.7
  MinimalModbus-0.6
  setuptools-5.1
  RTDE_Python
)

for pkg in "${PACKAGES[@]}"; do
  echo "Installing $pkg ..."
  cd "$pkg"
  python setup.py install
  cd ..
done

echo "All packages installed successfully."