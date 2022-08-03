import json
from brownie import accounts, Contract
import random
from math import ceil, floor
import time


def split_args(args):
    l_arg = args.split(',')
    acc = l_arg[0].strip()
    market = l_arg[1].strip()
    col_lower = int(l_arg[2].strip())
    col_upper = int(l_arg[3].strip())
    lev = int(l_arg[4].strip())
    gap = int(l_arg[5].strip())
    return acc, market, col_lower, col_upper, lev, gap


def get_market_abi():
    f = open('scripts/constants/mock/market_abi.json')
    return json.load(f)


def get_contract_adds():
    f = open('scripts/constants/contracts.json')
    return json.load(f)


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def init_contract(cont_name):
    cont_add = get_contract_adds()
    cont = load_contract(cont_add[cont_name])
    return cont


def approve_spending(token, amount, spender, acc):
    token.approve(spender, amount, {'from': acc})


def build(args):
    acc, market_addr, col_lower, col_upper,\
        lev, gap_time = split_args(args)
    acc = accounts.load(acc)
    market_abi = get_market_abi()
    market = Contract.from_abi('market', market_addr, market_abi)
    ovl = init_contract('ovl_token')

    while True:
        is_long = random.choice([True, False])
        col = floor(random.uniform(col_lower, col_upper))
        notional = (col * lev)/1e18
        fee = ceil((notional * market.params(11))/1e18)
        approve_spending(ovl, ceil(col + fee), market, acc)
        if is_long:
            price = (2**256)-1
        else:
            price = 0
        tx = market.build(col, lev, is_long, price, {'from': acc})
        pos_id = tx.events['Build']['positionId']
        print(f'Position id: {pos_id}')
        print(f'Col: {col}')
        print(f'Lev: {lev}')
        print(f'Is long: {is_long}')
        print(f'Sleeping for {gap_time} secs')
        time.sleep(gap_time)
