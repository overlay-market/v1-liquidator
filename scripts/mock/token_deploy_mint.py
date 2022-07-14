from brownie import (
        accounts, web3)


def split_args(args):
    l_arg = args.split(',')
    acc = l_arg[0].strip()
    token_cont = l_arg[1].strip()
    return acc, token_cont


def main(args):
    acc, cont = split_args(args)
    acc = accounts.load(acc)

    exec(f'from brownie import {cont}')

    tok = eval(cont).deploy({'from': acc}, publish_source=True)
    print(f'Contract created at {tok.address}')
    tok.grantRole(web3.solidityKeccak(['string'], ["MINTER"]),
                  acc.address, {'from': acc})
    tok.mint(acc, 1e9 * 1e18, {'from': acc})
    print('Minted 1e9 tokens to input account')
