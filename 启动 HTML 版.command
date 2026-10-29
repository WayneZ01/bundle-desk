#!/bin/zsh
cd "${0:A:h}"
ARCH="$(uname -m)"
PYTHON="$PWD/runtime/$ARCH/python/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  echo "缺少内置运行时。请使用完整发行包。"
  read -k 1
  exit 1
fi
exec "$PYTHON" app/server.py
