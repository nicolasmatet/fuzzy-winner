import logging

import networkx as nx
import numpy as np
from matplotlib import pyplot as plt
from scipy import sparse
from scipy.optimize import fmin_l_bfgs_b

import entityModule
import transactionModule

logger = logging.getLogger(__name__)


def compute_taxes(transfer_ratio, *args):
    entities_network = args[0]
    set_transaction_transfer_ratio(entities_network, transfer_ratio)
    compute_transactions_amounts(entities_network)
    compute_entities_final_accounts_balance(entities_network)
    compute_entities_taxes(entities_network)
    total_tax_amount = get_total_taxes_amount(entities_network)
    return total_tax_amount


def optimize_transfer_ratio(entities_network):
    x0 = np.array(list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio").values()))
    bounds = np.array(list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio_bounds").values()))
    fmin_l_bfgs_b(compute_taxes, x0, args=tuple([entities_network]), bounds=bounds, approx_grad=True, epsilon=1e-12)


def compute_initial_taxes(entities_network):
    x0 = np.array(list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio").values()))
    return compute_taxes(x0, entities_network)


def set_transaction_transfer_ratio(entities_network, transfer_rates_list):
    new_transfer_rates = dict(zip(entities_network.get_network().edges_iter(keys=True), transfer_rates_list))
    nx.set_edge_attributes(entities_network.get_network(), "transfer_ratio", new_transfer_rates)


def compute_transactions_amounts(entities_network):
    """
    solve the (dual) linear problem M*X=V where:
    M = Identity matrix - transaction matrix
    X is the vector of transaction amounts
    V is the vector of exogen revenue for reference accounts group of each transaction * transactin transfer ratio
    For a desciption of the transaction matrix see " get_transaction_matrix"
    :param entities_network:
    :return: None
    """
    transfer_ratio_vector = np.array(
        list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio").values()))
    transaction_matrix = entities_network.transaction_matrix.multiply(transfer_ratio_vector)
    identity_matrix = sparse.csr_matrix(sparse.identity(transaction_matrix.shape[0]))
    transaction_amount_matrix = sparse.csr_matrix.transpose(identity_matrix - transaction_matrix)
    exogen_revenue_share_vector = entities_network.exogen_revenues_vector * transfer_ratio_vector
    transaction_amounts = sparse.linalg.spsolve(transaction_amount_matrix, exogen_revenue_share_vector)
    transaction_amount_dict = dict(zip(entities_network.get_network().edges_iter(keys=True), transaction_amounts))
    nx.set_edge_attributes(entities_network.get_network(), "computed_amount", transaction_amount_dict)


def compute_entities_taxes(entities_network):
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        entityModule.compute_taxes(entity_data)

def get_total_taxes_amount(entities_network):
    total_taxes_amount = 0
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        total_taxes_amount += entity_data.get("paid_taxes", 0)
    return total_taxes_amount


def get_total_taxable_income(entities_network):
    total_taxable_income = 0
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        total_taxable_income += entityModule.get_taxable_income(entity_data)
    return total_taxable_income


def get_mean_tax_rate(entities_network):
    total_taxes_amount = get_total_taxes_amount(entities_network)
    total_taxable_income = get_total_taxable_income(entities_network)
    if total_taxable_income == 0:
        return 0
    return total_taxes_amount / total_taxable_income


def compute_entities_final_accounts_balance(entities_network):
    entities_network.cash_in_exogen_revenues()
    entities_network.make_internal_transactions()


def draw_entity_network(entities_network):
    network = entities_network.get_network()
    pos = nx.spring_layout(network)
    nx.draw(network, pos)
    node_labels = entities_network.get_account_balances_dict()
    nx.draw_networkx_labels(network, pos, labels=node_labels)
    nx.draw_networkx_edge_labels(network, pos, edge_labels={})
    plt.show()


class EntitiesNetwork:
    def __init__(self):
        self._network = nx.MultiDiGraph()
        self.transaction_matrix = None
        self.exogen_revenues_vector = None

    def add_entity(self, entity_id, entity_dict, accounts_digraph):
        entity_dict["accounts"] = accounts_digraph
        self._network.add_node(entity_id, entity_dict)

    def get_network(self):
        return self._network

    def add_transaction(self, initiator_entity, destinatary_entity, transaction_dict):
        self._network.add_edge(initiator_entity, destinatary_entity, **transaction_dict)

    def update_network(self):
        self.transaction_matrix = self.get_transaction_matrix()
        self.exogen_revenues_vector = self.get_exogen_revenues_vector()

    def get_account_balances_dict(self):
        account_balance_dict = dict()
        for entity in self._network.nodes(data=True):
            entity_id = entity[0]
            entity_data = entity[-1]
            account_balance_dict[entity_id] = entityModule.get_accounts_total(entity_data, "final_balance")
        return account_balance_dict

    def cash_in_exogen_revenues(self):
        for entity in self.get_network().nodes(data=True):
            entity_data = entity[-1]
            entityModule.cash_in_exogen_revenues(entity_data)

    def make_internal_transactions(self):
        for entity_id in self._network.nodes():
            outbound_operations = self.get_network().out_edges(entity_id, data=True)
            inbound_operations = self.get_network().in_edges(entity_id, data=True)
            entity = self.get_network().node[entity_id]
            accounts = entity.get("accounts")
            transactionModule.make_transactions(accounts, outbound_operations, operation="debit")
            transactionModule.make_transactions(accounts, inbound_operations, operation="credit")

    def get_transaction_matrix(self):
        """
        the transaction matrix is the matrix in which each row and column represents a transaction
        the matrix component (i,j) is 1 if the transaction i is received by one of the reference accounts
        of the transaction j
        :param :
        :return: nb_transaction * nb_transaction sparse matrix
        """
        rows = []
        for transaction in self.get_network().edges(data=True, keys=True):
            rows.append(self.get_transaction_matrix_row(transaction))
        return sparse.csr_matrix.transpose(sparse.vstack(rows))

    def get_transaction_matrix_row(self, reference_transaction):
        reference_transaction_data = reference_transaction[-1]
        initiator_entity_id = reference_transaction[0]
        initiator_entity = self.get_network().node[initiator_entity_id]
        reference_accounts = transactionModule.get_reference_accounts(initiator_entity, reference_transaction_data)
        row = np.zeros(len(self.get_network().edges()))
        for idx, transaction in enumerate(self.get_network().edges(data=True)):
            if transaction[-1].get("destinatary_account") in reference_accounts \
                    and transaction[1] == initiator_entity_id:
                row[idx] = 1
        return sparse.csr_matrix(row)

    def get_exogen_revenues_vector(self):
        exogen_revenues = []
        for transaction in self._network.edges(data=True):
            transaction_data = transaction[-1]
            initiator_entity_data = self._network.node[transaction[0]]
            initiator_entity = self._network.node[transaction[0]]
            reference_accounts = transactionModule.get_reference_accounts(initiator_entity, transaction_data)
            total_exogen_revenue = \
                entityModule.get_accounts_total(initiator_entity_data, "exogen_revenue", accounts=reference_accounts)
            exogen_revenues.append(total_exogen_revenue)
        return np.array(exogen_revenues)
