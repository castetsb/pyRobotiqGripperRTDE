#!/bin/bash

set -e  # stop on first error

PACKAGES=(
  setuptools-5.1
  six-1.17.0
  pyserial-3.4
  pymodbus-2.3.0
  UrRtde-2.7.12
)

for pkg in "${PACKAGES[@]}"; do
  echo "Processing $pkg ..."

  if [ -f "$pkg.tar.gz" ]; then
    echo "Extracting $pkg.tar.gz ..."
    tar -xzf "$pkg.tar.gz"
  else
    echo "No .tar.gz archive found for $pkg"
    exit 1
  fi

  if [ ! -d "$pkg" ]; then
    echo "Directory $pkg not found after extraction!"
    exit 1
  fi

  cd "$pkg"
  echo "Installing $pkg ..."
  python setup.py install
  cd ..

  echo "Removing extracted folder $pkg ..."
  rm -rf "$pkg"

done

echo "All packages installed successfully."
