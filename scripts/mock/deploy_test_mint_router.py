from brownie import TestMintRouter, accounts


def main(acc):
    acc = accounts.load(acc)
    TestMintRouter.deploy({"from": acc})
