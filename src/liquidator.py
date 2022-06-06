def get_all_positions():
    '''
    Get list of all existing positions.
    '''
    return


def is_position_liq(pos):
    '''
    Flag if position is liquidatable.
    '''
    return


def tx_liq_position(pos):
    '''
    1. Send tx to liquidate position.
    2. Store tx hash in list/dict
    '''
    return


def get_pending_txs():
    '''
    Get list of liquidation txs that are pending/failed.
    '''
    return


def get_pending_liq_txs():
    '''
    Get list of txs that are pending/failed but still liquidatable.
    '''
    return


def main():
    # List of all positions
    pos = get_all_positions()
    
    # List of new liquidatable txs
    liq_pos = []
    for p in pos:
        if is_position_liq(p):
            liq_pos.append(p)
    
    # List of new and previously pending/failed liquidatable txs
    liq_pos = liq_pos + get_pending_liq_txs()

    # Send liquidation txs
    for p in liq_pos:
        tx_liq_position(p)
