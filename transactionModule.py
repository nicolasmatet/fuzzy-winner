import secrets

def get_transaction_dict(initiator_account, destinatary_account, transfer_ratio, **kargs):
    transation_id = kargs.get("transaction_id", secrets.token_urlsafe(16))
    return {"id":transation_id,
            "initiator_account":initiator_account,
            "destinatary_account":destinatary_account,
            "transfer_ratio":transfer_ratio }


class Transaction:
    def __init__(self, **kargs):
        self.__dict__.update(**kargs)
