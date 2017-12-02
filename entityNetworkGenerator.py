from entityModule import get_entity_dict, add_account
import entitiesNetworkModule
import numpy as np
from transactionModule import get_transaction_dict
from accountsModule import get_account_dict, create_accounts_digraph
import logging
from scipy.optimize import fmin_l_bfgs_b, fmin_tnc
import networkx as nx

logging.basicConfig(level=logging.INFO)

entities_to_add = [
    get_entity_dict(1, 0.1),
    get_entity_dict(2, 0.08),
    get_entity_dict(3, 0.4),
    get_entity_dict(4, 0.05)
]

accounts = [
    get_account_dict(1, "acc1", 0, 100),
    get_account_dict(1, "acc2", 0, 200),
    get_account_dict(2, "acc1", 0, 0),
    get_account_dict(3, "acc1", 0, 0),
    get_account_dict(4, "acc1", 0, 0)

]

transactions_to_add = [
    {"initiator_entity": 1, "destinatary_entity": 2,
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, reference_accounts=[], transfer_ratio_bounds=(0, 0.1))},
    {"initiator_entity": 1, "destinatary_entity": 3,
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, reference_accounts=["acc2"],
                                         transfer_ratio_bounds=(0, 0.1))},
    {"initiator_entity": 3, "destinatary_entity": 4,
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 1))},
]

entities_network = entitiesNetworkModule.EntitiesNetwork()
for entity_dict in entities_to_add:
    entity_id = entity_dict.get("id")
    entities_network.add_entity(entity_id, entity_dict, create_accounts_digraph([]))
for account_data in accounts:
    owner_entity_data = entities_network.get_network().node[account_data.get("owner_id")]
    add_account(owner_entity_data, account_data)
for transaction_to_add in transactions_to_add:
    initiator_entity = transaction_to_add.get("initiator_entity")
    destinatary_entity = transaction_to_add.get("destinatary_entity")
    transactions_dict = transaction_to_add.get("transaction")
    entities_network.add_transaction(initiator_entity, destinatary_entity, transactions_dict)

entitiesNetworkModule.compute_initial_taxes(entities_network)
print("initial mean tax rate = {:.2f} %".format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network)))
entitiesNetworkModule.optimize_transfer_ratio(entities_network)
print("optimized mean tax rate = {:.2f} %".format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network)))
entitiesNetworkModule.draw_entity_network(entities_network)
