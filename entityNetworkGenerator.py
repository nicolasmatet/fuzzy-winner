from entityModule import Entity, get_entity_dict
import entitiesNetworkModule
from transactionModule import Transaction, get_transaction_dict
import networkx as nx
from scipy import sparse
import numpy as np

entities_to_add = [
    get_entity_dict(1, 100),
    get_entity_dict(2, 100),
    get_entity_dict(3, 100)
]

transactions_to_add = [
    {"destinatary_entity": 3, "initiator_entity": 1, "transaction":get_transaction_dict(1, 1, 0.2)},
    {"destinatary_entity": 3, "initiator_entity": 2, "transaction":get_transaction_dict(1, 1, 0.3)},
    {"destinatary_entity": 3, "initiator_entity": 1, "transaction": get_transaction_dict(1, 1, 0.2)},
    {"destinatary_entity": 3, "initiator_entity": 2, "transaction": get_transaction_dict(1, 1, 0.3)},
]

entities_network = entitiesNetworkModule.EntitiesNetwork()
for entity_dict in entities_to_add:
    entity_object = Entity(**entity_dict)
    entities_network.add_entity(entity_object.get_id(), entity_object)
for transaction_to_add in transactions_to_add:
    initiator_entity = transaction_to_add.get("initiator_entity")
    destinatary_entity = transaction_to_add.get("destinatary_entity")
    transactions_dict = transaction_to_add.get("transaction")
    entities_network.add_transaction(destinatary_entity,initiator_entity, transactions_dict)

adjacency_matrix = nx.adjacency_matrix(entities_network.get_network(), weight="transfer_ratio")
identity_matrix = sparse.csr_matrix(sparse.identity(adjacency_matrix.shape[0]))
transaction_matrix = identity_matrix - adjacency_matrix
exogen_revenue_vector = entities_network.get_exogen_revenue_vector()
revenues = sparse.linalg.spsolve(transaction_matrix, exogen_revenue_vector)

print(revenues)
