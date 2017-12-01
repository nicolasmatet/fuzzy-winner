import networkx as nx
import numpy as np
from scipy import sparse
import logging
import entityModule
import matplotlib
from scipy.optimize import fmin_l_bfgs_b
from matplotlib import pyplot as plt

logger = logging.getLogger(__name__)

def compute_taxes(transfer_ratio, *args):
    entities_network = args[0]
    set_transaction_transfer_ratio(entities_network, transfer_ratio)
    compute_entities_revenues(entities_network)
    compute_transactions_amounts(entities_network)
    compute_entities_final_accounts_balance(entities_network)
    compute_entities_taxes(entities_network)
    total_tax_amount = get_total_taxes_amount(entities_network)
    return total_tax_amount

def optimize_transfer_ratio(entities_network):
    x0 = np.array(list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio").values()))
    bounds = np.array(list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio_bounds").values()))
    fmin_l_bfgs_b(compute_taxes, x0, args = tuple([entities_network]),  bounds=bounds, approx_grad=True, epsilon=1e-12)

def compute_initial_taxes(entities_network):
    x0 = np.array(list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio").values()))
    return compute_taxes(x0, entities_network)

def compute_entities_revenues(entities_network):
    adjacency_matrix = nx.adjacency_matrix(entities_network.get_network(), weight="transfer_ratio")
    transaction_matrix = sparse.csr_matrix.transpose(adjacency_matrix)
    identity_matrix = sparse.csr_matrix(sparse.identity(adjacency_matrix.shape[0]))
    revenue_matrix = identity_matrix - transaction_matrix
    exogen_revenue_vector = entities_network.get_exogen_revenues_vector()
    revenues = sparse.linalg.spsolve(revenue_matrix, exogen_revenue_vector)
    revenue_dict = dict(zip(entities_network.get_network().nodes(), revenues))
    nx.set_node_attributes(entities_network.get_network(), "computed_revenue", revenue_dict)

def set_transaction_transfer_ratio(entities_network, transfer_rates_list):
    new_transfer_rates = dict(zip(entities_network.get_network().edges_iter(keys=True), transfer_rates_list))
    nx.set_edge_attributes(entities_network.get_network(), "transfer_ratio", new_transfer_rates)

def compute_transactions_amounts(entities_network):
    computed_transactions_amounts = dict()
    for edge in entities_network.get_network().edges_iter(data=True, keys=True):
        initiator_entity_id = edge[0]
        destinatary_entity_id = edge[1]
        edge_key = edge[2]
        transaction_data = edge[3]
        initiator_entity = entities_network.get_network().node[initiator_entity_id]
        transfer_ratio = transaction_data.get("transfer_ratio")
        transaction_amount = entities_network.compute_transaction_amount(initiator_entity, transfer_ratio)
        computed_transactions_amounts[(initiator_entity_id, destinatary_entity_id, edge_key)] = transaction_amount
    nx.set_edge_attributes(entities_network.get_network(), "computed_amount", computed_transactions_amounts)


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
    # edge_labels = nx.get_edge_attributes(network, 'computed_amount')
    nx.draw_networkx_edge_labels(network, pos, edge_labels={})
    plt.show()


class EntitiesNetwork:
    def __init__(self):
        self._network = nx.MultiDiGraph()

    def add_entity(self, entity_id, entity_dict, accounts_digraph):
        entity_dict["accounts"] = accounts_digraph
        self._network.add_node(entity_id, entity_dict)

    def get_network(self):
        return self._network

    def add_transaction(self, initiator_entity, destinatary_entity, transaction_dict):
        self._network.add_edge(initiator_entity, destinatary_entity, **transaction_dict)

    def get_exogen_revenues_vector(self):
        exogen_revenues = []
        for entity in self._network.nodes(data=True):
            entity_data = entity[-1]
            exogen_revenues.append(entityModule.get_accounts_total(entity_data, "exogen_revenue"))
        return np.array(exogen_revenues)

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
            self.make_transactions(accounts, outbound_operations, operation="debit")
            self.make_transactions(accounts, inbound_operations, operation="credit")


    def make_transactions(self, accounts, transactions_list, operation="debit"):
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


    def compute_transaction_amount(self, reference_entity, transfer_ratio):
        return reference_entity.get("computed_revenue") * transfer_ratio
