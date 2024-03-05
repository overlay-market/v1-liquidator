import asyncio
from telegram import Bot
import traceback
from concurrent.futures import ThreadPoolExecutor
from itertools import compress, chain as ichain
from brownie import (
    accounts, Contract,
    chain, multicall
    )
import json
import math
import time
import os
import sys
import datetime

MAX_ATTEMPTS = 5


def print_w_time(string):
    gmt_offset = datetime.timezone(datetime.timedelta(hours=0))
    current_time =\
        datetime.datetime.now(gmt_offset).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time} GMT] {string}", flush=True)


def get_constants_path():
    script_path = os.path.realpath(__file__)
    repo = os.path.abspath(os.path.join(script_path, os.pardir, os.pardir))
    return repo + '/scripts/constants/'


def init_account(acc, password):
    acc = accounts.load(acc, password=password)
    return acc


def read_json(filename):
    constants_path = get_constants_path()
    f = open(constants_path + filename)
    return json.load(f)


def get_constants(chain):
    const = read_json('constants.json')
    return const[chain]


def get_abis():
    return read_json('abis.json')


def load_contract(address):
    try:
        return Contract(address)
    except Exception as e:
        print_w_time(f'Unable to load address {address} from cache')
        print_w_time(f"Error: {str(e)}")
        try:
            return Contract.from_explorer(address)
        except Exception as e:
            print_w_time(
                f'Unable to load address {address} from block explorer'
            )
            print_w_time(f"Error: {str(e)}")
            abis = get_abis()
            if address not in abis.keys():
                print_w_time(
                    f'Address abi unavailable. Unable to load {address}'
                )
                sys.exit()
            else:
                abi = abis[address]
                return Contract.from_abi('contract', address, abi)


def get_market_contracts(markets):
    return [load_contract(mkt) for mkt in markets]


def init_state(chain, market_subset):
    consts = get_constants(chain)
    ovl = load_contract(consts['ovl_token'])
    state = load_contract(consts['ovl_market_state'])
    markets = get_market_contracts(consts['markets'][market_subset])
    multicall = consts['multicall']  # Addr used as string
    start_block = int(consts['start_block'][market_subset])
    return ovl, state, markets, multicall, start_block


def try_with_backoff(func):
    '''
    Try running function with exponential backoff.
    Used for making Web API calls here
    '''
    tries = 1
    while tries > 0:
        try:
            result = func()
            tries = 0
        except Exception as e:
            err_msg = str(e)
            print_w_time(f"Error: {err_msg}")
            backoff_interval = (2 ** tries) / 10
            tries += 1
            print_w_time(f'Sleeping for {backoff_interval} secs')
            time.sleep(backoff_interval)
    return result


def get_event_args(markets, start_block, end_block):
    args = []
    for mkt in markets:
        args.append((mkt, start_block, end_block))
    return args


def get_events(args):
    (market, start_block, end_block) = args
    events = try_with_backoff(lambda: market.events.get_sequence(
                                    from_block=start_block, 
                                    to_block=end_block))
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
        try:
            Contract(pos[0]).liquidate(
                pos[1], pos[2],
                {'from': acc, 'priority_fee': "2 gwei"})
            liqd_pos.append(pos)
        except ValueError:
            error_message = traceback.format_exc()
            print_w_time(f"Unable to liquidate: {error_message}")
        time.sleep(0.5)
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


def send_message(bot_message, notify):
    telegram = read_json('telegram.json')
    print_w_time(bot_message)
    asyncio.run(
        send_telegram_message(
            bot_message,
            telegram['telegram_token'],
            telegram['telegram_chat_id'],
            notify
        )
    )


async def send_telegram_message(message, bot_token, chat_id, notify):
    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        disable_notification=notify
        )


def main(acc_name, chain_name, market_subset):
    secrets = read_json('secrets.json')
    attempt_count = 0
    last_notification_timestamp = 0
    market_subset_int = int(market_subset)
    while True:
        try:
            # Initialize account and contracts
            acc = init_account(acc_name, secrets['brownie_pass'])
            print_w_time(f'Account {acc.address} loaded')
            _, state, markets, multicall, start_block = init_state(
                chain_name,
                market_subset_int
                )

            all_pos = []
            prev_liqd_pos = []

            markets_str = '\n'.join(
                [f'{market.address}' for market in markets]
                )
            bot_message = (
                f'LIQUIDATOR {acc.address} STARTED\n'
                f'FOR MARKETS {markets_str}\n'
            )
            send_message(bot_message, False)
            while True:
                # if ovl.balanceOf(acc) >= params['max_ovl']:
                #     swap_to_eth(ovl.balanceOf(acc), params['slippage'], weth,
                #     ovl, swap_router, pool, acc)
                end_block = chain.height
                if end_block - start_block > 100_000:
                    end_block = start_block + 100_000
                if start_block > end_block:
                    continue

                results = []
                events_args = get_event_args(markets, start_block, end_block)
                print_w_time(
                    f'Obtained data from blocks {start_block} to {end_block}'
                )
                with ThreadPoolExecutor() as executor:
                    for item in executor.map(get_events, events_args):
                        results.append(item)
                build_events, liq_events, unw_events = arrange_events(results)
                all_pos += get_all_pos(build_events)
                liq_pos = get_liq_pos(liq_events)
                unw_pos = get_unw_pos(unw_events)
                remove_pos = liq_pos + unw_pos + prev_liqd_pos
                all_pos = list(set(all_pos) - set(remove_pos))
                print_w_time(f'Tracking {len(all_pos)} positions')
                # Notify to telegram the amount of positions being tracked
                # once every 6 hours
                if time.time() - last_notification_timestamp > 21600:
                    bot_message = (
                        f'LIQUIDATOR {acc.address} TRACKING {len(all_pos)} '
                        f'POSITIONS'
                    )
                    send_message(bot_message, True)
                    last_notification_timestamp = time.time()
                # Divide all_pos into chunks of 1000
                liqable_pos = []
                for i in range(0, len(all_pos), 1000):
                    liqable_pos += try_with_backoff(
                        lambda: is_liquidatable(
                            all_pos[i:i+1000], state, multicall)
                    )
                print_w_time(f'{len(liqable_pos)} positions to liquidate')
                if len(liqable_pos) > 0:
                    prev_liqd_pos += liquidate_pos(liqable_pos, acc)
                start_block = end_block + 1
                attempt_count = 0
                # Inform if balance is low once every 6 hours
                alert_time = time.time()
                if acc.balance() < 5e17 and time.time() - alert_time > 21600:
                    bot_message = (
                        f'''
                        LIQUIDATOR {acc.address} LOW BALANCE
                        Current balance: {acc.balance() / 1e18} ETH
                        '''
                    )
                    send_message(bot_message, True)
        except Exception:
            error_message = traceback.format_exc()
            bot_message = (
                f'''
                LIQUIDATOR {acc.address} STOPPED
                Error: {error_message}
                Attempting to restart in 5 minutes...
                '''
            )
            send_message(bot_message, False)
            attempt_count += 1
            time.sleep(300)
            if attempt_count >= MAX_ATTEMPTS:
                bot_message = (
                    f'''
                    LIQUIDATOR {acc.address} STOPPED after {MAX_ATTEMPTS}
                     attempts
                    Maximum attempt limit reached. Exiting...
                    '''
                )
                send_message(bot_message, False)
                break
