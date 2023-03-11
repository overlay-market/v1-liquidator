# v1-liquidator

Liquidator bot for V1


## Requirements

To run the project you need:

- Python >=3.7.0 local development environment
- [Brownie](https://github.com/eth-brownie/brownie) local environment setup
- Set env variables for [Etherscan API](https://etherscan.io/apis), [Infura](https://eth-brownie.readthedocs.io/en/stable/network-management.html?highlight=infura%20environment#using-infura) and [Alchemy] (https://www.alchemy.com/): `ETHERSCAN_TOKEN`, `WEB3_INFURA_PROJECT_ID`, `ALCHECMY_API_KEY`
- Local Ganache environment installed


## Installation

Using [Poetry](https://python-poetry.org/docs/) for dependencies. Install poetry

```
curl -sSL https://install.python-poetry.org | python3 -
```

Clone the repo, then, to install dependencies

```
poetry install
```

within the local dir.

## Brownie setup

1. Create an account using brownie and fund it for gas (more info [here](https://eth-brownie.readthedocs.io/en/stable/account-management.html#local-accounts)):

```
brownie accounts generate my_account
```
2. Infura node (default choice by brownie) is sometimes problematic on arbitrum. So set up brownie to use alchemy node for arbitrum
```
brownie networks add Arbitrum arbi-alc host=https://arb-mainnet.g.alchemy.com/v2/ALCHEMY_API_KEY_HERE name=arbi-alc chainid=42161 explorer=https://api.arbiscan.io
```
## Run liquidator

Add or remove market and/or other contracts from `scripts/constants/constants.json` if required.

Run liquidator on arbitrum:
```
brownie run liquidator.py main my_account arbitrum --network arbi-alc
```
Run liquidator on Eth L1:
```
brownie run liquidator.py main my_account ethereum --network mainnet
```