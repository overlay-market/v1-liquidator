from brownie import (
    accounts
    )


def main():
    # Get the first account
    account = accounts.load("acc", 'overlay')
    # Send 4 ether to the account
    account.transfer('0x521f917DF92A822059d4BABD7BC48c214FDb4694', '4 ether')