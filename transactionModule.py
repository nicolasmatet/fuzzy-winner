import secrets


def get_transaction_dict(initiator_account, destinatary_account, transfer_ratio, **kargs):
    transation_id = kargs.get("transaction_id", secrets.token_urlsafe(16))
    transfer_ratio_bounds = kargs.get("transfer_ratio_bounds", (0, 1))
    return {"id": transation_id,
            "initiator_account": initiator_account,
            "destinatary_account": destinatary_account,
            "transfer_ratio": transfer_ratio,
            "transfer_ratio_bounds": transfer_ratio_bounds}
