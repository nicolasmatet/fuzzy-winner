import logging

import entitiesNetworkModule
import transactionModule
from accountsModule import get_account_dict, create_accounts_digraph
from entityModule import get_entity_dict, add_account
from transactionModule import get_transaction_dict

logging.basicConfig(level=logging.INFO)

entities_to_add = [
    get_entity_dict(1, 0.1),
    get_entity_dict(2, 0.08),
    get_entity_dict(3, 0.02),
    get_entity_dict(4, 0.05),
    get_entity_dict("holding", 0.0)
]

accounts = [
    get_account_dict(1, "acc1", 0, 100),
    get_account_dict(2, "acc1", 0, 100),
    get_account_dict(3, "acc1", 0, 100),
    get_account_dict(4, "acc1", 0, 200),
    get_account_dict("holding", "acc1", 0, 0)
]

transactions_to_add = [
    {"initiator_entity": 1, "destinatary_entity": "holding",
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 0.1))},
    {"initiator_entity": 2, "destinatary_entity": "holding",
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 0.1))},
    {"initiator_entity": "holding", "destinatary_entity": 3,
     "transaction": get_transaction_dict("acc1", "acc1", 0.1,
                                         transfer_ratio_calculation=transactionModule.TRANSFER_RATIO_THEIR)},
    {"initiator_entity": "holding", "destinatary_entity": 4,
     "transaction": get_transaction_dict("acc1", "acc1", 0.1,
                                         transfer_ratio_calculation=transactionModule.TRANSFER_RATIO_THEIR)},
    {"initiator_entity": 4, "destinatary_entity": 3, "transaction": get_transaction_dict("acc1", "acc1", 0.2)},

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
entities_network.update_network()

entitiesNetworkModule.compute_initial_taxes(entities_network)
print("initial mean tax rate = {:.2f} %".format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network)))
entitiesNetworkModule.optimize_transfer_ratio(entities_network)
print("optimized mean tax rate = {:.2f} %".format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network)))
# graph_name = os.path.join("gml", secrets.token_urlsafe(16) + ".graphml")
# nx.write_graphml(entities_network.get_network(), graph_name)
entitiesNetworkModule.draw_entity_network(entities_network)
