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
    logger.debug("transfer ratios = {}".format(str(transfer_ratio)))
    entities_network = args[0]
    computed_transfer_ratio = compute_computed_transfer_ratios(entities_network, transfer_ratio)
    set_transaction_transfer_ratio(entities_network, transfer_ratio, computed_transfer_ratio)
    compute_transactions_amounts(entities_network)
    compute_entities_revenue(entities_network)
    compute_entities_final_accounts_balance(entities_network)
    compute_entities_taxes(entities_network)
    total_tax_amount = get_total_taxes_amount(entities_network)
    logger.debug("total tax = {:.2f}".format(total_tax_amount))
    return total_tax_amount


def compute_computed_transfer_ratios(entities_network, constant_transfer_ratios):
    computed_transfer_ratios = np.array([0] * entities_network.number_of_computed_transfer_ratio)
    if not len(computed_transfer_ratios):
        return []
    res = 1
    while res > 1e-6:
        set_transaction_transfer_ratio(entities_network, constant_transfer_ratios, computed_transfer_ratios)
        compute_transactions_amounts(entities_network)
        compute_entities_revenue(entities_network)
        new_computed_transfer_ratios = (entities_network.get_computed_transfer_ratios() + computed_transfer_ratios) / 2
        res = max(abs(new_computed_transfer_ratios - computed_transfer_ratios))
        computed_transfer_ratios = new_computed_transfer_ratios
    return computed_transfer_ratios

def optimize_transfer_ratio(entities_network):
    x0 = entities_network.get_constant_transfer_ratios()
    bounds = entities_network.get_transfer_ratio_bounds()
    fmin_l_bfgs_b(compute_taxes, x0, args=tuple([entities_network]), bounds=bounds, approx_grad=True, epsilon=1e-12)


def compute_initial_taxes(entities_network):
    x0 = entities_network.get_constant_transfer_ratios()
    return compute_taxes(x0, entities_network)


def set_transaction_transfer_ratio(entities_network, constant_transfer_rates_list, computed_transfer_ratio_list):
    transfer_ratios = []
    constant_transfer_rates = iter(constant_transfer_rates_list)
    computed_transfer_ratio = iter(computed_transfer_ratio_list)
    for transaction in entities_network.get_network().edges(data=True, keys=True):
        if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_OUR:
            transfer_ratios.append(next(constant_transfer_rates))
        if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_THEIR:
            transfer_ratios.append(next(computed_transfer_ratio))
    transfer_ratios_dict = dict(zip(entities_network.get_network().edges_iter(keys=True), transfer_ratios))
    nx.set_edge_attributes(entities_network.get_network(), "transfer_ratio", transfer_ratios_dict)



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


def compute_entities_revenue(entities_network):
    revenue_dict = dict()
    for entity_id in entities_network.get_network().nodes():
        inbound_transactions = entities_network.get_network().in_edges(entity_id, data=True)
        entity = entities_network.get_network().node[entity_id]
        revenue = entityModule.set_revenue(entity, inbound_transactions)
        revenue_dict[entity_id] = revenue

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
        self.number_of_constant_transfer_ratio = 0
        self.number_of_computed_transfer_ratio = 0

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
        self.number_of_constant_transfer_ratio = self.counts_constant_transfer_ratios()
        self.number_of_computed_transfer_ratio = len(self._network.edges()) - self.number_of_constant_transfer_ratio

    def counts_constant_transfer_ratios(self):
        number_of_constant_transfer_ratios = 0
        transfer_ratio_calculation_dict = nx.get_edge_attributes(self._network, "transfer_ratio_calculation")
        for transfer_ratio_calculation in transfer_ratio_calculation_dict.values():
            if transfer_ratio_calculation == transactionModule.TRANSFER_RATIO_OUR:
                number_of_constant_transfer_ratios += 1
        return number_of_constant_transfer_ratios

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
        reference_entity_id = transactionModule.get_reference_entity_id(reference_transaction)
        reference_entity_data = self._network.node[reference_entity_id]
        reference_accounts = transactionModule.get_reference_accounts(reference_entity_data, reference_transaction_data)
        row = np.zeros(len(self.get_network().edges()))
        for idx, transaction in enumerate(self.get_network().edges(data=True)):
            if transaction[1] == reference_entity_id and \
                    transaction[-1].get("destinatary_account") in reference_accounts:
                row[idx] = 1
        return sparse.csr_matrix(row)

    def get_exogen_revenues_vector(self):
        exogen_revenues = []
        for transaction in self._network.edges(data=True):
            reference_entity_id = transactionModule.get_reference_entity_id(transaction)
            reference_entity_data = self._network.node[reference_entity_id]
            reference_accounts = transactionModule.get_reference_accounts(reference_entity_data, transaction[-1])
            total_exogen_revenue = \
                entityModule.get_accounts_total(reference_entity_data, "exogen_revenue", accounts=reference_accounts)
            exogen_revenues.append(total_exogen_revenue)
        return np.array(exogen_revenues)

    def get_constant_transfer_ratios(self):
        computed_transfer_ratios = []
        transactions = self._network.edges(data=True)
        for transaction in transactions:
            if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_OUR:
                computed_transfer_ratios.append(transaction[-1].get("transfer_ratio"))
        return np.array(computed_transfer_ratios)

    def get_transfer_ratio_bounds(self):
        transfer_ratio_bounds = []
        transactions = self._network.edges(data=True)
        for transaction in transactions:
            if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_OUR:
                transfer_ratio_bounds.append(transaction[-1].get("transfer_ratio_bounds"))
        return np.array(transfer_ratio_bounds)


    def get_computed_transfer_ratios(self):
        computed_transfer_ratios = []
        transfer_ratio_calculations = nx.get_edge_attributes(self._network, "transfer_ratio_calculation")
        for transaction, transfer_ratio_calculation in transfer_ratio_calculations.items():
            if transfer_ratio_calculation == transactionModule.TRANSFER_RATIO_OUR:
                continue
            computed_transfer_ratio = self.get_transaction_computed_transfer_ratio(transaction)
            computed_transfer_ratios.append(computed_transfer_ratio)
        return np.array(computed_transfer_ratios)

    def get_transaction_computed_transfer_ratio(self, transaction):
        initiator_entity_id = transaction[0]
        initiator_entity = self._network.node[initiator_entity_id]
        initiator_entity_revenue = initiator_entity.get("computed_revenue")
        initiator_outbound_operations = self.get_network().out_edges(initiator_entity_id, data=True, keys=True)
        outbound_entity_revenues = 0
        for initiator_outbound_operation in initiator_outbound_operations:
            accounts = transactionModule.get_reference_accounts(initiator_entity, initiator_outbound_operation[-1])
            destinatary_entity_data = self._network.node[initiator_outbound_operation[1]]
            outbound_entity_revenues += entityModule.get_accounts_total(destinatary_entity_data, "computed_revenue",
                                                                        accounts=accounts)
        return initiator_entity_revenue / outbound_entity_revenues if outbound_entity_revenues != 0 else 0
