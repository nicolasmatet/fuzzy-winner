from entityModule import  get_entity_dict
import entitiesNetworkModule
from transactionModule import get_transaction_dict
from accountsModule import get_account_dict, create_accounts_digraph, add_account

entities_to_add = [
    get_entity_dict(1),
    get_entity_dict(2),
    get_entity_dict(3),
    get_entity_dict(4)
]

accounts = [
get_account_dict(1,"acc1", 0,100),
get_account_dict(2,"acc1", 0,100),
get_account_dict(3,"acc1", 0,100),
get_account_dict(4,"acc1", 0,100)
]

transactions_to_add = [
    {"destinatary_entity": 3, "initiator_entity": 1, "transaction":get_transaction_dict("acc1", "acc1", 0.2)},
    {"destinatary_entity": 3, "initiator_entity": 2, "transaction":get_transaction_dict("acc1", "acc1", 0.3)},
    {"destinatary_entity": 4, "initiator_entity": 3, "transaction": get_transaction_dict("acc1", "acc1", 0.5)},
    {"destinatary_entity": 1, "initiator_entity": 4, "transaction": get_transaction_dict("acc1", "acc1", 0.5)},
    {"destinatary_entity": 2, "initiator_entity": 4, "transaction": get_transaction_dict("acc1", "acc1", 0.5)}
]

entities_network = entitiesNetworkModule.EntitiesNetwork()
for entity_dict in entities_to_add:
    entity_id = entity_dict.get("id")
    entities_network.add_entity(entity_id, entity_dict, create_accounts_digraph([]))
for account_dict in accounts:
    owner_entity = entities_network.get_network().node[account_dict.get("owner_id")]
    add_account(owner_entity.get("accounts"), account_dict)
for transaction_to_add in transactions_to_add:
    initiator_entity = transaction_to_add.get("initiator_entity")
    destinatary_entity = transaction_to_add.get("destinatary_entity")
    transactions_dict = transaction_to_add.get("transaction")
    entities_network.add_transaction(destinatary_entity,initiator_entity, transactions_dict)

entitiesNetworkModule.compute_entities_revenues(entities_network)
entitiesNetworkModule.compute_transactions_amounts(entities_network)
entitiesNetworkModule.compute_entities_accounts_balance(entities_network)
entitiesNetworkModule.draw_entity_network(entities_network)