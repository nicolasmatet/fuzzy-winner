import logging

import networkx as nx

from . import transactionModule

logger = logging.getLogger(__name__)


def get_entity_dict(entity_id, tax_rate):
    return {"id": str(entity_id).strip().upper(), "tax_rate": float(tax_rate), "computed_revenue": 0, "paid_taxes": 0}


def get_tax_amount(entity_data, include_negative_cash_flow):
    tax_rate = entity_data.get("tax_rate", 0)
    if include_negative_cash_flow:
        taxable_income = get_balance_variation(entity_data)
    else:
        taxable_income = get_taxable_income(entity_data)

    return float(tax_rate * taxable_income)


def get_balance_variation(entity_data):
    initial_balance = get_accounts_total(entity_data, "initial_balance")
    final_balance = get_accounts_total(entity_data, "final_balance")
    return final_balance - initial_balance


def get_taxable_income(entity_data):
    initial_balance = get_accounts_total(entity_data, "initial_balance")
    final_balance = get_accounts_total(entity_data, "final_balance")
    return max(final_balance - initial_balance, 0)


def set_revenue(entity_data, inbound_transactions):
    """
    Compute the revenue of each account inside the entity as well as the total revenue of the entity
    (which is the sum of each account revenue)
    :param entity_data:
    :param inbound_transactions:
    :return:
    """
    revenues = nx.get_node_attributes(entity_data.get("accounts"), "exogen_revenue")
    for transaction in inbound_transactions:
        transaction_amount = transaction[-1].get("computed_amount")
        destinatary_account = transaction[-1].get("destinatary_account")
        revenues[destinatary_account] += transaction_amount
    nx.set_node_attributes(entity_data.get("accounts"), "computed_revenue", revenues)
    entity_data["computed_revenue"] = sum(revenues.values())


def set_spendings(entity_data, outbound_transactions):
    """
    Compute the spendings of each account inside the entity as well as the total spending of the entity
    (which is the sum of each account spending)
    :param entity_data:
    :param outbound_transactions:
    :return:
    """
    spendings = nx.get_node_attributes(entity_data.get("accounts"), "exogen_spending")
    for transaction in outbound_transactions:
        transaction_amount = transaction[-1].get("computed_amount")
        initiator_account = transaction[-1].get("initiator_account")
        spendings[initiator_account] += transaction_amount
    nx.set_node_attributes(entity_data.get("accounts"), "computed_spending", spendings)
    entity_data["computed_spending"] = sum(spendings.values())


def compute_taxes(entity_data, include_negative_cash_flow=False):
    tax_amount = get_tax_amount(entity_data, include_negative_cash_flow)
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


def get_total_exogen_transfer(entity_data, transaction_data):
    reference_accounts = transactionModule.get_reference_accounts(entity_data, transaction_data)
    if transaction_data.get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_THEIR:
        return get_accounts_total(entity_data, "exogen_spending", accounts=reference_accounts)
    return get_accounts_total(entity_data, "exogen_revenue", accounts=reference_accounts)


def add_account(entity_data, account_data):
    accounts = entity_data.get("accounts")
    accounts.add_node(account_data.get("id"), **account_data)


def cash_in_exogen_revenues(entity_data):
    accounts = entity_data.get("accounts")
    for account in accounts.nodes(data=True):
        account_data = account[-1]
        account_data["final_balance"] = account_data["initial_balance"] + account_data.get("exogen_revenue", 0)


def get_entities_labels(entities_network):
    id_dict = nx.get_node_attributes(entities_network.get_network(), "id")
    balances_dict = entities_network.get_account_balances_dict()
    taxes_dict = nx.get_node_attributes(entities_network.get_network(), "paid_taxes")
    revenues_dict = nx.get_node_attributes(entities_network.get_network(), "computed_revenue")
    spending_dict = nx.get_node_attributes(entities_network.get_network(), "computed_spending")
    labels = ["{}\n"
              "revenue: {:.2f}\n"
              "spendings: {:.2f}\n"
              "taxes: {:.2f}\n"
              "balance:{:.2f}".format(node_id, revenue, spending, taxes_dict, balance)
              for node_id, revenue, spending, taxes_dict, balance
              in zip(id_dict.values(),
                     revenues_dict.values(),
                     spending_dict.values(),
                     taxes_dict.values(),
                     balances_dict.values())]
    node_labels = dict(zip(entities_network.get_network().nodes(), labels))
    return node_labels


def get_entities_tooltips(entities_network):
    tax_rate_dict = nx.get_node_attributes(entities_network.get_network(), "tax_rate")
    labels = ["tax rate: {:.2f} %".format(100 * tax_rate) for tax_rate in tax_rate_dict.values()]
    entities_tooltips = dict(zip(entities_network.get_network().nodes(), labels))
    return entities_tooltips
