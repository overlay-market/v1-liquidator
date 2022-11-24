from brownie import accounts, Contract
import json
import math
import time


def build_pos(market):
    pos = market.build()
    return pos


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


def approve_spending(token, amount, spender, acc):
    token.approve(spender, amount, {'from': acc})


def build(ovl, market, col, lev, is_long, acc):
    notional = col * lev
    fee = notional * market.params(11)
    approve_spending(ovl, math.ceil(col + fee), market, acc)
    if is_long:
        price = (2**256)-1
    else:
        price = 0
    tx = market.build(col, lev, is_long, price, {'from': acc})

    # Unable use `tx.return_value` for pos_id on rinkeby
    # since rinkeby node doesn't allow that
    pos_id = tx.events['Build']['positionId']
    return pos_id


def swap_attrs(pool, weth, ovl, lev, is_long):
    col_size_ratio = (1e18/lev)
    cz_ratio_w_buffer = col_size_ratio * 1.3

    weth_res = weth.balanceOf(pool)
    ovl_res = ovl.balanceOf(pool)
    k = weth_res * ovl_res
    p = ovl_res/weth_res
    if is_long:
        new_weth_res = math.sqrt(k/((1-cz_ratio_w_buffer)*p))
        size = new_weth_res - weth_res
        new_p = k/(new_weth_res**2)

    else:
        new_ovl_res = math.sqrt(k*((1+cz_ratio_w_buffer)*p))
        size = new_ovl_res - ovl_res
        new_p = (new_ovl_res**2)/k
    print(f'Old price: {p}')
    print(f'New price: {new_p}')
    return size


def swap(router, pool, ovl, weth, lev, is_long, acc):
    size = swap_attrs(pool, weth, ovl, lev, is_long)

    if is_long:
        token_in = weth
        token_out = ovl
    else:
        token_in = ovl
        token_out = weth

    params = (token_in.address, token_out.address, 3000,
              acc.address, math.ceil(time.time() + 600),
              size, 0, 0)

    router.exactInputSingle(params, {'from': acc})


def split_args(args):
    l_arg = args.split(',')
    col = int(l_arg[0].strip())
    lev = int(l_arg[1].strip())
    long = True if l_arg[2].strip().lower() == 'true' else False
    return col, lev, long


def main(args):
    # get input args
    overlay_col, overlay_lev, overlay_long = split_args(args)

    # initialize account and contracts
    acc = init_account()
    market, pool, swap_router, ovl, weth, state = init_contracts()

    # build position
    pos_id = build(ovl, market, overlay_col, overlay_lev, overlay_long, acc)
    print(f'Position id: {pos_id}')

    # swap spot to so overlay position is liquidatable
    swap(swap_router, pool, ovl, weth, overlay_lev, overlay_long, acc)

    # check if liqable
    liq_flag = state.liquidatable(market, acc, pos_id)
    print(f'Liquidatable? {liq_flag}')
