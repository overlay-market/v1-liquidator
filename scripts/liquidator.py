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


def get_constants(chain):
    f = open('scripts/constants/constants.json')
    const = json.load(f)
    return const[chain]


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def get_market_contracts(markets):
    return [load_contract(mkt) for mkt in markets]


def init_state(chain):
    consts = get_constants(chain)
    ovl = load_contract(consts['ovl_token'])
    weth = load_contract(consts['weth_token'])
    state = load_contract(consts['ovl_market_state'])
    markets = get_market_contracts(consts['markets'])
    multicall = consts['multicall']  # Addr used as string
    start_block = int(consts['start_block'])
    return ovl, weth, state, markets, multicall, start_block


def get_event_args(markets, start_block, end_block):
    args = []
    for mkt in markets:
        args.append((mkt, start_block, end_block))
    return args


def get_events(args):
    (market, start_block, end_block) = args
    tries = 1
    while tries > 0:
        try:
            events = market.events.get_sequence(
                                    from_block=start_block,
                                    to_block=end_block)
            tries = 0
        except Exception as e:
            err_msg = str(e)
            print(f"Error: {err_msg}")
            backoff_interval = (2 ** tries) / 10
            tries += 1
            print(f'Sleeping for {backoff_interval} secs')
            time.sleep(backoff_interval)
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


def is_liquidatable(positions, state, mc_addr):
    multicall(address=mc_addr)
    with multicall:
        is_liq = [state.liquidatable(pos[0], pos[1], pos[2])
                  for pos in positions]
    return list(compress(positions, is_liq))


def get_liq_fee(positions, state, mc_addr):
    multicall(address=mc_addr)
    with multicall:
        fee = [state.liquidationFee(pos[0], pos[1], pos[2])
               for pos in positions]
    pos_fee = [list(i) for i in zip(positions, fee)]
    pos_fee.sort(key=lambda x: int(x[1]), reverse=True)
    return pos_fee


def liquidate_pos(positions, acc):
    liqd_pos = []
    for pos in positions:
        Contract(pos[0]).liquidate(
            pos[1], pos[2],
            {'from': acc, 'priority_fee':"2 gwei"})
        liqd_pos.append(pos)
        time.sleep(1)
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


def main(acc_name, chain_name):
    # Initialize account and contracts
    acc = init_account(acc_name)
    print(f'Account {acc.address} loaded')
    _, _, state, markets, multicall, start_block = init_state(chain_name)

    all_pos = []
    prev_liqd_pos = []
    while True:
        # if ovl.balanceOf(acc) >= params['max_ovl']:
        #     swap_to_eth(ovl.balanceOf(acc), params['slippage'], weth, ovl,
        #                 swap_router, pool, acc)
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

        liqable_pos = is_liquidatable(all_pos, state, multicall)
        liqable_pos = get_liq_fee(liqable_pos, state, multicall)
        liqable_pos = [i[0] for i in liqable_pos if i[1] >= 0]
        print(f'{len(liqable_pos)} positions to liquidate')
        if len(liqable_pos) == 0:
            continue
        prev_liqd_pos += liquidate_pos(liqable_pos, acc)
        start_block = end_block + 1
