import secrets


def get_transaction_dict(initiator_account, destinatary_account, transfer_ratio, **kargs):
    transation_id = kargs.get("transaction_id", secrets.token_urlsafe(16))
    transfer_ratio_bounds = kargs.get("transfer_ratio_bounds", None)
    transfer_ratio_calculation = kargs.get("transfer_ratio_calculation", "share_of_initiator_revenue")
    reference_accounts = set(kargs.get("reference_accounts", []))
    return {"id": transation_id,
            "initiator_account": initiator_account,
            "destinatary_account": destinatary_account,
            "transfer_ratio": transfer_ratio,
            "transfer_ratio_bounds": transfer_ratio_bounds,
            "reference_accounts": reference_accounts,
            "transfer_ratio_calculation": transfer_ratio_calculation,}

def get_reference_accounts(initiator_entity, transaction_data):
    reference_accounts = transaction_data.get("reference_accounts", None)
    if reference_accounts is None or not len(reference_accounts):
        reference_accounts = set(initiator_entity.get("accounts").nodes())
    return reference_accounts
