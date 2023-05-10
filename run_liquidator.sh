#!/bin/bash

export PATH=/home/ubuntu/.vscode-server/bin/252e5463d60e63238250799aef7375787f68b4ee/bin/remote-cli:/home/ubuntu/.local/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
cd "$(dirname "$0")"
poetry run brownie run liquidator.py main my_account arbitrum --network arbi-alc