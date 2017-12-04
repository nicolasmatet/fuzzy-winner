import logging
import secrets

logger = logging.getLogger(__name__)

TRANSFER_RATIO_OUR = "OUR"
TRANSFER_RATIO_THEIR = "THEIR"


def get_transaction_dict(initiator_account, destinatary_account, transfer_ratio, **kargs):
    """
    Sets the initial attributes of a transaction.
    :param initiator_account: name of the account inside the initiator entity from which the money is debited
    :param destinatary_account: name of the account inside the destinatary entity on which the money is credited
    :param transfer_ratio: share of the final reference accounts revenues that is transfer by this transaction
    :param kargs:
            id: id of the transaction, if not set, default value is a random string
            transfer_ratio_bounds: tuple or None. Min and Max bounds of admissible transfer ratio for this transaction.
                                    None means no limits. Default is (0, 1)
            reference_accounts: list of accounts id. The amount of money transfered by the transaction is transfer_ratio * revenue,
                                where revenue is the sum of the revenues of the reference accounts.
                                All references accounts must be inside the reference entity
                                Reference entity is initiator entity is transfer mode is "OUR".
                                Reference entity is destinatary entity if transfer mode is "THEIR".
                                Empty list [] means that all accounts inside the reference entity are used. Default is [].
            transfer_ratio_calculation: mode of transfer. Posible values = "OUR", "THEIR".
                                        In "OUR" mode, transaction transfer an amount corresponding to a given share of the initiator entity revenue.
                                        In "THEIR" mode, transaction transfer an amount corresponding to a given share of the destinatary revenue.
                                        "THEIR" mode is useful to share an amount of money between destinataries depending on their respective revenues
                                        Default is "OUR"
    :return:
    """
    transation_id = kargs.get("transaction_id", secrets.token_urlsafe(16))
    transfer_ratio_bounds = kargs.get("transfer_ratio_bounds", (0, 1))
    transfer_ratio_calculation = kargs.get("transfer_ratio_calculation", TRANSFER_RATIO_OUR)
    reference_accounts = set(kargs.get("reference_accounts", []))
    return {"id": transation_id,
            "initiator_account": initiator_account,
            "destinatary_account": destinatary_account,
            "transfer_ratio": transfer_ratio,
            "transfer_ratio_bounds": transfer_ratio_bounds,
            "reference_accounts": reference_accounts,
            "transfer_ratio_calculation": transfer_ratio_calculation,
            }


def get_reference_entity_id(transaction_with_data):
    transaction_data = transaction_with_data[-1]
    reference_entity_id = transaction_with_data[0]
    if transaction_data.get("transfer_ratio_calculation", TRANSFER_RATIO_OUR) == TRANSFER_RATIO_THEIR:
        reference_entity_id = transaction_with_data[1]
    return reference_entity_id


def get_reference_accounts(reference_entity_data, transaction_data):
    reference_accounts = transaction_data.get("reference_accounts", None)
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
