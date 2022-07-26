import json
from brownie import accounts, Contract
import random
from math import sqrt
import time


def split_args_lp(args):
    l_arg = args.split(',')
    acc = l_arg[0].strip()
    pool = l_arg[1].strip()
    amount = int(l_arg[2].strip())
    appr = l_arg[3].strip()
    return acc, pool, amount, appr


def split_args_swap(args):
    l_arg = args.split(',')
    acc = l_arg[0].strip()
    pool = l_arg[1].strip()
    pi_lower = int(l_arg[2].strip())
    pi_upper = int(l_arg[3].strip())
    gap = int(l_arg[4].strip())
    appr = l_arg[5].strip()
    return acc, pool, pi_lower, pi_upper, gap, appr


def get_pool_abi():
    f = open('scripts/constants/mock/pool_abi.json')
    return json.load(f)


def get_contract_adds():
    f = open('scripts/constants/mock/contracts_mock.json')
    return json.load(f)


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def init_contracts():
    cont_add = get_contract_adds()
    mint_router = load_contract(cont_add['mint_router'])
    return mint_router


def lp(args):
    acc, pool_addr, amount, appr_reqd = split_args_lp(args)
    acc = accounts.load(acc)
    pool_abi = get_pool_abi()
    pool = Contract.from_abi('pool', pool_addr, pool_abi)
    mint_router = init_contracts()

    tok1 = Contract(pool.token0())
    tok2 = Contract(pool.token1())

    if eval(appr_reqd):
        tok1.approve(mint_router, tok1.balanceOf(acc), {'from': acc})
        tok2.approve(mint_router, tok2.balanceOf(acc), {'from': acc})

    mint_router.mint(pool.address, -36000, 36000, amount, {"from": acc})


def swap(args):
    acc, pool_addr, pi_lower, pi_upper,\
        gap_time, appr_reqd = split_args_swap(args)
    acc = accounts.load(acc)
    pool_abi = get_pool_abi()
    pool = Contract.from_abi('pool', pool_addr, pool_abi)
    mint_router = init_contracts()

    tok1 = Contract(pool.token0())
    tok2 = Contract(pool.token1())

    if eval(appr_reqd):
        tok1.approve(mint_router, tok1.balanceOf(acc), {'from': acc})
        tok2.approve(mint_router, tok2.balanceOf(acc), {'from': acc})

    while True:
        # 'o' suffix denotes "old" state, prior to swapping
        xo = tok1.balanceOf(pool)
        yo = tok2.balanceOf(pool)
        k = xo * yo
        po = yo/xo
        print(f'Price pre-swap: {po}')

        pi_rand = random.uniform(pi_lower/100, pi_upper/100)
        swap_dir = random.choice([True, False])
        print(f'Exp price delta: {pi_rand*100}%')
        print(f'Swapping x for y: {swap_dir}')
        if swap_dir:
            p = po * (1-pi_rand)
        else:
            p = po * (1+pi_rand)

        yn = sqrt(k*p)
        xn = sqrt(k/p)

        if swap_dir:
            size = xn - xo
        else:
            size = yn - yo
        mint_router.swap(pool, swap_dir, size, {'from': acc})

        pn = tok2.balanceOf(pool)/tok1.balanceOf(pool)
        print(f'Price post-swap: {pn}')
        print(f'Obs price delta: {((pn - po)/po) * 100}%')
        print(f'Sleeping for {gap_time} secs')
        time.sleep(gap_time)
