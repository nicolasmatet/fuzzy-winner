import networkx as nx
import numpy as np
from scipy import sparse
import logging
import entityModule
import matplotlib
from matplotlib import pyplot as plt

logger = logging.getLogger(__name__)


def compute_entities_revenues(entities_network):
    adjacency_matrix = nx.adjacency_matrix(entities_network.get_network(), weight="transfer_ratio")
    identity_matrix = sparse.csr_matrix(sparse.identity(adjacency_matrix.shape[0]))
    transaction_matrix = identity_matrix - adjacency_matrix
    exogen_revenue_vector = entities_network.get_exogen_revenues_vector()
    revenues = sparse.linalg.spsolve(transaction_matrix, exogen_revenue_vector)
    revenue_dict =  dict(zip(entities_network.get_network().nodes(), revenues))
    nx.set_node_attributes(entities_network.get_network(), "computed_revenue", revenue_dict)


def compute_transactions_amounts(entities_network):
    computed_amounts = dict()
    for edge in entities_network.get_network().edges_iter(data=True, keys=True):
        destinatary_entity_id = edge[0]
        initiator_entity_id = edge[1]
        edge_key = edge[2]
        transaction_data = edge[3]
        initiator_entity = entities_network.get_network().node[initiator_entity_id]
        transfer_ratio = transaction_data.get("transfer_ratio")
        transaction_amount = _compute_transaction_amount(initiator_entity, transfer_ratio)
        computed_amounts[(destinatary_entity_id, initiator_entity_id, edge_key)] = transaction_amount
    nx.set_edge_attributes(entities_network.get_network(), "computed_amount", computed_amounts)

def compute_entities_accounts_balance(entities_network):
    _cash_in_exogen_revenues(entities_network)
    _make_internal_transactions(entities_network)

def _cash_in_exogen_revenues(entities_network):
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        entityModule.cash_in_exogen_revenues(entity_data)

def _make_internal_transactions(entities_network):
    for entity_id in entities_network.get_network().nodes():
        outbound_operations = entities_network.get_network().in_edges(entity_id, data=True)
        inbound_operations = entities_network.get_network().out_edges(entity_id, data=True)
        entity = entities_network.get_network().node[entity_id]
        accounts = entity.get("accounts")
        _make_transactions(accounts, outbound_operations, operation="debit")
        _make_transactions(accounts, inbound_operations, operation="credit")

def _make_transactions(accounts, transactions_list, operation="debit"):
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

def _compute_transaction_amount(reference_entity, transfer_ratio):
    return reference_entity.get("computed_revenue") * transfer_ratio


def draw_entity_network(entities_network):
    network = entities_network.get_network()
    pos = nx.spring_layout(network)
    nx.draw(network, pos)
    node_labels = entities_network.get_account_balances_dict()
    nx.draw_networkx_labels(network, pos, labels=node_labels)
    edge_labels = nx.get_edge_attributes(network, 'computed_amount')
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

    def add_transaction(self, destinatary_entity, initiator_entity, transaction_dict):
        self._network.add_edge(destinatary_entity, initiator_entity, **transaction_dict)

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