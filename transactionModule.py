import logging
import secrets

logger = logging.getLogger(__name__)

TRANSFER_RATIO_OUR = "our_revenue"
TRANSFER_RATIO_THEIR = "their_revenue"


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
            "transfer_ratio_calculation": transfer_ratio_calculation, }


def get_reference_entity_id(transaction_with_data):
    transaction_data = transaction_with_data[-1]
    reference_entity_id = transaction_with_data[0]
    if transaction_data.get("transfer_ratio_calculation", TRANSFER_RATIO_OUR) == TRANSFER_RATIO_THEIR:
        reference_entity_id = transaction_with_data[1]
    return reference_entity_id


def get_reference_accounts(reference_entity_data, transaction_with_data):
    reference_accounts = transaction_with_data.get("reference_accounts", None)
    if reference_accounts is None or not len(reference_accounts):
        reference_accounts = set(reference_entity_data.get("accounts").nodes())
    return reference_accounts


def make_transactions(accounts, transactions_list, operation="debit"):
    for transaction in transactions_list:
        transaction_data = transaction[-1]
        initiator_account = transaction_data.get("initiator_account")
        account = accounts.node[initiator_account]
        if operation == "debit":
            account["final_balance"] -= transaction_data.get("computed_amount")
        elif operation == "credit":
            account["final_balance"] += transaction_data.get("computed_amount")
        else:
            logger.error("Unknown operation {}".format(operation))
