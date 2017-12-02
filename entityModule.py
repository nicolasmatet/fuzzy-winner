import logging
logger = logging.getLogger(__name__)

def get_entity_dict(entity_id, tax_rate):
    return {"id": entity_id, "tax_rate": tax_rate, "computed_revenue":0, "paid_taxes":0}


def get_tax_amount(entity_data):
    tax_rate = entity_data.get("tax_rate", 0)
    taxable_income = get_taxable_income(entity_data)
    return tax_rate * taxable_income


def get_taxable_income(entity_data):
    initial_balance = get_accounts_total(entity_data, "initial_balance")
    final_balance = get_accounts_total(entity_data, "final_balance")
    return max(final_balance - initial_balance, 0)


def compute_taxes(entity_data):
    tax_amount = get_tax_amount(entity_data)
    entity_data["paid_taxes"] = tax_amount
    logger.debug("Entity {} paid taxes = {:.2f}".format(entity_data.get("id"), tax_amount))


def get_accounts_total(entity_data, quantity, accounts=None):
    total_value = 0
    all_accounts = entity_data.get("accounts").nodes(data=True)
    for account in all_accounts:
        if accounts is not None and account[0] not in accounts:
            continue
        account_data = account[-1]
        total_value += account_data.get(quantity)
    return total_value


def add_account(entity_data, account_data):
    accounts = entity_data.get("accounts")
    accounts.add_node(account_data.get("id"), **account_data)


def cash_in_exogen_revenues(entity_data):
    accounts = entity_data.get("accounts")
    for account in accounts.nodes(data=True):
        account_data = account[-1]
        account_data["final_balance"] = account_data["initial_balance"] + account_data.get("exogen_revenue", 0)

