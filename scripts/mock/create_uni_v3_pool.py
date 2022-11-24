import json
from brownie import accounts, Contract


def split_args(args):
    l_arg = args.split(',')
    acc = l_arg[0].strip()
    tok1 = l_arg[1].strip()
    tok2 = l_arg[2].strip()
    return acc, tok1, tok2


def get_pool_abi():
    f = open('scripts/constants/mock/pool_abi.json')
    return json.load(f)


def main(args):
    acc, tok1, tok2 = split_args(args)
    acc = accounts.load(acc)

    tok1 = Contract(tok1)
    tok2 = Contract(tok2)

    factory = Contract.from_explorer(
                        '0x1F98431c8aD98523631AE4a59f267346ea31F984')

    tx = factory.createPool(tok1, tok2, 3000, {"from": acc})
    pool_addr = tx.events['PoolCreated']['pool']
    pool_abi = get_pool_abi()

    pool = Contract.from_abi('pool', pool_addr, pool_abi)
    pool.initialize(7.9220240490215315e28, {"from": acc})  # price = 1
    pool.increaseObservationCardinalityNext(510, {"from": acc})
