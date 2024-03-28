# v1-liquidator

Liquidator bot for V1

## Requirements

To run the project you need:

- Python >=3.7.0 local development environment
- [Brownie](https://github.com/eth-brownie/brownie) local environment setup
- Set env variable for [Arbiscan API](https://etherscan.io/apis): `ARBISCAN_TOKEN`
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

Add account password to `scripts/constants/brownie_pass.txt`

2. Alchemy node (default choice by brownie) is sometimes problematic on arbitrum. So set up brownie to use alchemy node for arbitrum

Arbitrum Mainnet

```
brownie networks add Arbitrum arbi-alc host=https://arb-mainnet.g.alchemy.com/v2/\$WEB3_ALCHEMY_PROJECT_ID name=arbi-alc chainid=42161 explorer=https://api.arbiscan.io
```

Arbitrum Sepolia

```
brownie networks modify arbitrum-sepolia host="https://arb-sepolia.g.alchemy.com/v2/\$WEB3_ALCHEMY_PROJECT_ID"
```

Example running the command `brownie networks list True`

```
Arbitrum
  ├─Mainnet
  │ ├─id: arbitrum-main
  │ ├─chainid: 42161
  │ ├─explorer: https://api.arbiscan.io/api
  │ ├─host: https://arbitrum-mainnet.infura.io/v3/$WEB3_ALCHEMY_PROJECT_ID
  │ ├─multicall2: 0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858
  │ └─provider: alchemy
  └─Testnet
    ├─id: arbitrum-sepolia
    ├─chainid: 421614
    ├─explorer: https://api-sepolia.arbiscan.io/api
    ├─host: https://arb-sepolia.g.alchemy.com/v2/$WEB3_ALCHEMY_PROJECT_ID
    ├─multicall2: 0xA115146782b7143fAdB3065D86eACB54c169d092
    └─provider: alchemy
```

## Run liquidator on development enviroment

Add or remove market and/or other contracts from `scripts/constants/constants.json` if required.

Run liquidator on arbitrum:

```
brownie run liquidator.py main my_account arbitrum --network arbi-alc
```

Run liquidator on Eth L1:

```
brownie run liquidator.py main my_account ethereum --network mainnet
```

## Run liquidator on server

```
tmux new-session -d -s liquidator1

tmux send-keys -t liquidator1 "poetry run bash -c 'export $WEB3_ALCHEMY_PROJECT_ID=[REPLACE WITH API KEY] && brownie run liquidator.py main liquidator arbitrum-sepolia 0 --network arbi-sepolia'" C-m

tmux new-session -d -s liquidator2

tmux send-keys -t liquidator2 "poetry run bash -c 'export $WEB3_ALCHEMY_PROJECT_ID=[REPLACE WITH API KEY] && brownie run liquidator.py main liquidator1 arbitrum-sepolia 1 --network arbi-sepolia'" C-m
```

## MANDATORY JSON FILES

Under the folder `scripts/constants/`

### secrets.json

```json
{
  "brownie_pass": "password"
}
```

### telegram.json

```json
{
  "telegram_token": "7141444343:AAFRafp9KEi6KwoS63esc73bL0bOiaYSqLQ",
  "telegram_chat_id": "-1002017678300",
  "muted_telegram_token": "6888005028:AAEtxN7fR5NOVfw-bd-Uo1HYo5JPZ3qf_GA",
  "muted_telegram_chat_id": "-1002030677057"
}
```

- Muted channels are for messages that are periodically sent to the telegram channel which is mutter
- Not muted is for importan messages like errors or low balance in the bot wallet.
