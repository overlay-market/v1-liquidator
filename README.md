# v1-liquidator

Liquidator bot for V1


## Requirements

To run the project you need:

- Python >=3.7.0 local development environment
- [Brownie](https://github.com/eth-brownie/brownie) local environment setup
- Set env variables for [Etherscan API](https://etherscan.io/apis) and [Infura](https://eth-brownie.readthedocs.io/en/stable/network-management.html?highlight=infura%20environment#using-infura): `ETHERSCAN_TOKEN` and `WEB3_INFURA_PROJECT_ID`
- Local Ganache environment installed


## Installation

Using [Poetry](https://github.com/python-poetry/poetry) for dependencies. Install with `pipx`

```
pipx install poetry
```

Clone the repo, then

```
poetry install
```

within the local dir.
