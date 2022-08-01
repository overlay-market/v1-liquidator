# Almost exact copy of https://github.com/overlay-market/v1-core/blob/7408e3e704afaba548ab2af0d70f47566f73a017/scripts/create.py # NOQA
# Changes marked with "Changed"

import click

from brownie import Contract, accounts, network


# TODO: change
FACTORY = "0xE79BD387201EC0c33c9539294056652bC3b32B7D"


def main():
    """
    Creates a new OverlayV1Market through factory
    `deployMarket()` function.
    """
    click.echo(f"You are using the '{network.show_active()}' network")
    gov = accounts.load(click.prompt(
        "Account", type=click.Choice(accounts.load())))

    # instantiate the factory contract
    # Changed
    factory = Contract.from_explorer(FACTORY)

    # assemble feed params for deployMarket
    feed_factory = click.prompt("feedFactory (address)")
    feed = click.prompt("feed (address)")

    # assemble risk params for deployMarket
    params = [
        "k (uint256)",
        "lmbda (uint256)",
        "delta (uint256)",
        "capPayoff (uint256)",
        "capNotional (uint256)",
        "capLeverage (uint256)",
        "circuitBreakerWindow (uint256)",
        "circuitBreakerMintTarget (uint256)",
        "maintenanceMarginFraction (uint256)",
        "maintenanceMarginBurnRate (uint256)",
        "liquidationFeeRate (uint256)",
        "tradingFeeRate (uint256)",
        "minCollateral (uint256)",
        "priceDriftUpperLimit (uint256)",
        "averageBlockTime (uint256)"
    ]
    args = [click.prompt(f"{param}") for param in params]

    click.echo(
        f"""
        OverlayV1Market Parameters

        feedFactory (address): {feed_factory}
        feed (address): {feed}

        uint256[15] params
        k (uint256): {args[0]}
        lmbda (uint256): {args[1]}
        delta (uint256): {args[2]}
        capPayoff (uint256): {args[3]}
        capNotional (uint256): {args[4]}
        capLeverage (uint256): {args[5]}
        circuitBreakerWindow (uint256): {args[6]}
        circuitBreakerMintTarget (uint256): {args[7]}
        maintenanceMarginFraction (uint256): {args[8]}
        maintenanceMarginBurnRate (uint256): {args[9]}
        liquidationFeeRate (uint256): {args[10]}
        tradingFeeRate (uint256): {args[11]}
        minCollateral (uint256): {args[12]}
        priceDriftUpperLimit (uint256): {args[13]}
        averageBlockTime (uint256): {args[14]}
        """
    )

    if click.confirm("Deploy New Market"):
        tx = factory.deployMarket(feed_factory, feed, args, {"from": gov})
        tx.info()
        click.echo("Market deployed")