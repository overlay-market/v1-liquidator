from concurrent.futures import ThreadPoolExecutor
from itertools import compress, chain as ichain
from brownie import (
    accounts, Contract,
    chain, multicall
    )
import json
import math
import time


def init_account(acc):
    acc = accounts.load(acc)
    return acc


def get_params():
    '''
    markets: List of markets that bot will track
    max_ovl: Swap OVL to WETH when account balance crosses this limit
    slippage: Slippage allowed for OVL to WETH swap
    '''
    f = open('scripts/params/liquidator_params.json')
    return json.load(f)


def get_contract_adds():
    f = open('scripts/constants/contracts.json')
    return json.load(f)


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def get_market_contracts(markets):
    return [load_contract(mkt) for mkt in markets]


def init_contracts():
    cont_add = get_contract_adds()
    pool = load_contract(cont_add['univ3_market'])
    swap_router = load_contract(cont_add['swap_router'])
    ovl = load_contract(cont_add['ovl_token'])
    weth = load_contract(cont_add['weth_token'])
    state = load_contract(cont_add['ovl_market_state'])
    return pool, swap_router, ovl, weth, state


def get_event_args(markets, start_block, end_block):
    args = []
    for mkt in markets:
        args.append((mkt, start_block, end_block))
    return args


def get_events(args):
    (market, start_block, end_block) = args
    events = market.events.get_sequence(
                            from_block=start_block,
                            to_block=end_block)
    return events


def arrange_events(all_events):
    build_events = list(ichain(*[i.Build for i in all_events]))
    liq_events = list(ichain(*[i.Liquidate for i in all_events]))
    unw_events = list(ichain(*[i.Unwind for i in all_events]))
    return build_events, liq_events, unw_events


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


def swap_to_eth(amount, slippage, weth, ovl, router, pool, acc):
    price_s0 = pool.slot0()[0]
    ovl_price = (price_s0**2)/(2**(96*2))
    quote = ovl_price * amount/1e18
    min_amount = quote * (1 - slippage)
    params = (ovl.address, weth.address, 3000,
              acc.address, math.ceil(time.time() + 600),
              amount, 0, min_amount)

    # One-time approval of spending by router recommended.
    # Should be done outside this script.
    router.exactInputSingle(params, {'from': acc})


def main(args):
    # Initialize account and contracts
    acc = init_account(args)
    print(f'Account {acc.address} loaded')
    params = get_params()
    pool, swap_router, ovl, weth, state = init_contracts()
    markets = get_market_contracts(params['markets'])

    all_pos = []
    prev_liqd_pos = []
    start_block = 10885983
    while True:
        if ovl.balanceOf(acc) >= params['max_ovl']:
            swap_to_eth(ovl.balanceOf(acc), params['slippage'], weth, ovl,
                        swap_router, pool, acc)
        end_block = chain.height
        if start_block > end_block:
            continue

        results = []
        events_args = get_event_args(markets, start_block, end_block)
        with ThreadPoolExecutor() as executor:
            for item in executor.map(get_events, events_args):
                results.append(item)
        build_events, liq_events, unw_events = arrange_events(results)
        # events = get_events(markets, start_block, end_block)
        all_pos += get_all_pos(build_events)
        liq_pos = get_liq_pos(liq_events)
        unw_pos = get_unw_pos(unw_events)
        remove_pos = liq_pos + unw_pos + prev_liqd_pos
        all_pos = list(set(all_pos) - set(remove_pos))

        liqable_pos = is_liquidatable(all_pos, state)
        prev_liqd_pos += liquidate_pos(liqable_pos)
        start_block = end_block + 1
