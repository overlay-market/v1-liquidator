from itertools import compress
from brownie import (
    accounts, Contract,
    chain, multicall
    )
import json


def init_account():
    acc = accounts.load('brownie_acc1')
    return acc


def get_contract_adds():
    f = open('scripts/constants/contracts.json')
    return json.load(f)


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def init_contracts():
    cont_add = get_contract_adds()
    market = load_contract(cont_add['ovl_market'])
    pool = load_contract(cont_add['univ3_market'])
    swap_router = load_contract(cont_add['swap_router'])
    ovl = load_contract(cont_add['ovl_token'])
    weth = load_contract(cont_add['weth_token'])
    state = load_contract(cont_add['ovl_market_state'])
    return market, pool, swap_router, ovl, weth, state


def get_events(market, start_block, end_block):
    events = market.events.get_sequence(
                            from_block=start_block,
                            to_block=end_block)
    return events


def get_first_pos():
    return 0


def get_all_pos(bld_events):
    num = len(bld_events)
    pos = []
    if num > 0:
        for i in range(num):
            pos.append((bld_events[i].address,
                        bld_events[i].args.sender,
                        bld_events[i].args.positionId))
    return pos


def get_liq_pos(liq_events):
    num = len(liq_events)
    pos = []
    if num > 0:
        for i in range(num):
            pos.append((liq_events[i].address,
                        liq_events[i].args.sender,
                        liq_events[i].args.positionId))
    return pos


def get_unw_pos(unw_events):
    num = len(unw_events)
    pos = []
    if num > 0:
        for i in range(num):
            if unw_events[i].args.fraction == 1e18:
                pos.append((unw_events[i].address,
                            unw_events[i].args.sender,
                            unw_events[i].args.positionId))
    return pos


def is_liquidatable(positions, state):
    multicall(address='0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696')
    with multicall:
        is_liq = [state.liquidatable(pos[0], pos[1], pos[2])
                  for pos in positions]
    return list(compress(positions, is_liq))


def liquidate_pos(positions, market, acc):
    liqd_pos = []
    for pos in positions:
        market.liquidate(pos[1], pos[2], {'from': acc})
        liqd_pos.append(pos)
    return liqd_pos


def main():
    # Initialize account and contracts
    acc = init_account()
    print(f'Account {acc.address} loaded')
    market, pool, swap_router, ovl, weth, state = init_contracts()

    all_pos = []
    liqd_pos = []
    start_block = 10885983
    while True:
        end_block = chain.height
        if start_block > end_block:
            continue
        events = get_events(market, start_block, end_block)
        all_pos += get_all_pos(events.Build)
        liq_pos = get_liq_pos(events.Liquidate)
        unw_pos = get_unw_pos(events.Unwind)
        remove_pos = liq_pos + unw_pos + liqd_pos
        all_pos = list(set(all_pos) - set(remove_pos))

        liqable_pos = is_liquidatable(all_pos, state)
        liqd_pos += liquidate_pos(liqable_pos)
        start_block = end_block + 1
