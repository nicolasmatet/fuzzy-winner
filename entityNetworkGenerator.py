import logging

from accountsModule import get_account_dict
from entityModule import get_entity_dict
from transactionModule import get_transaction_dict

logging.basicConfig(level=logging.INFO)

entities_to_add = [
    get_entity_dict(1, 0.3),
    get_entity_dict(2, 0.25),
    get_entity_dict(3, 0.4),
    get_entity_dict(4, 0.23),
    get_entity_dict(5, 0.15),
    get_entity_dict("holding", 0.02)
]

accounts = [
    get_account_dict(1, "acc1", 0, 45, 0),
    get_account_dict(2, "acc1", 0, 50, 0),
    get_account_dict(3, "acc1", 0, 30, 0),
    get_account_dict(4, "acc1", 0, 80, 0),
    get_account_dict(5, "acc1", 0, 75, 0),
    get_account_dict("holding", "acc1", 0, 0, 0)
]

# transactions_to_add = [
#     {"initiator_entity": 1, "destinatary_entity": "holding",
#      "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 1))},
#     {"initiator_entity": 2, "destinatary_entity": "holding",
#      "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 1))},
#     {"initiator_entity": "holding", "destinatary_entity": 3,
#      "transaction": get_transaction_dict("acc1", "acc1", 0.5,
#                                          transfer_ratio_calculation=transactionModule.TRANSFER_RATIO_THEIR)},
#     {"initiator_entity": "holding", "destinatary_entity": 4,
#      "transaction": get_transaction_dict("acc1", "acc1", 0.5,
#                                          transfer_ratio_calculation=transactionModule.TRANSFER_RATIO_THEIR)},
# ]
transactions_to_add = [
    {"initiator_entity": 1, "destinatary_entity": "holding",
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 0.1))},
    {"initiator_entity": 2, "destinatary_entity": "holding",
     "transaction": get_transaction_dict("acc1", "acc1", 0.1, transfer_ratio_bounds=(0, 0.2))},
    {"initiator_entity": "holding", "destinatary_entity": 3,
     "transaction": get_transaction_dict("acc1", "acc1", 0.5, transfer_ratio_bounds=(0, 0.35))},
    {"initiator_entity": "holding", "destinatary_entity": 4,
     "transaction": get_transaction_dict("acc1", "acc1", 0.2, transfer_ratio_bounds=(0, 0.45))},
    {"initiator_entity": 4, "destinatary_entity": 5,
     "transaction": get_transaction_dict("acc1", "acc1", 0.3, transfer_ratio_bounds=(0, 0.3))},
    {"initiator_entity": 4, "destinatary_entity": 2,
     "transaction": get_transaction_dict("acc1", "acc1", 0.3, transfer_ratio_bounds=(0, 0.5))},
    {"initiator_entity": 3, "destinatary_entity": 1,
     "transaction": get_transaction_dict("acc1", "acc1", 0.3, transfer_ratio_bounds=(0, 0.3))},
    {"initiator_entity": 1, "destinatary_entity": 3,
     "transaction": get_transaction_dict("acc1", "acc1", 0.3, transfer_ratio_bounds=(0, 0.4))},
    {"initiator_entity": 2, "destinatary_entity": 5,
     "transaction": get_transaction_dict("acc1", "acc1", 0.3, transfer_ratio_bounds=(0, 0.3))},
    {"initiator_entity": 5, "destinatary_entity": 4,
     "transaction": get_transaction_dict("acc1", "acc1", 0.3, transfer_ratio_bounds=(0, 0.3))},
]


