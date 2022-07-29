# Almost exact copy of https://github.com/overlay-market/v1-core/blob/7408e3e704afaba548ab2af0d70f47566f73a017/scripts/feeds/uniswapv3/create.py # NOQA
# Changes marked with "Changed"

import click

from brownie import Contract, accounts, network


# TODO: change
UNIV3_FEED_FACTORY = "0x4658F04F8aafD1C3EB884F9Ad7085761eda83c9e"


def main():
    """
    Creates a new OverlayV1UniswapV3Feed through feed factory
    `deployFeed()` function.
    """
    click.echo(f"You are using the '{network.show_active()}' network")
    dev = accounts.load(click.prompt(
        "Account", type=click.Choice(accounts.load())))

    # instantiate the feed factory contract
    # Changed
    feed_factory = Contract.from_explorer(UNIV3_FEED_FACTORY)

    # assemble params for deployFeed
    params = ["marketBaseToken (address)", "marketQuoteToken (address)",
              "marketFee (uint24)", "marketBaseAmount (uint128)",
              "ovlXBaseToken (address)", "ovlXQuoteToken (address)",
              "ovlXFee (uint24)"]
    args = [click.prompt(f"{param}") for param in params]

    click.echo(
        f"""
        OverlayV1UniswapV3Feed Parameters

        marketBaseToken (address): {args[0]}
        marketQuoteToken (address): {args[1]}
        marketFee (uint24): {args[2]}
        marketBaseAmount (uint128): {args[3]}
        ovlXBaseToken (address): {args[4]}
        ovlXQuoteToken (address): {args[5]}
        ovlXFee (uint24): {args[6]}
        """
    )

    if click.confirm("Deploy New Feed"):
        tx = feed_factory.deployFeed(*args, {"from": dev})
        tx.info()
        click.echo("Uniswap V3 Feed deployed")
