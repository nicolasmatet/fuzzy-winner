def get_entity_dict(entity_id):
    return {"id":entity_id}



def get_accounts_total(entity_data, quantity):
    total_value = 0
    accounts = entity_data.get("accounts")
    for account in accounts.nodes(data=True):
        account_data = account[-1]
        total_value += account_data.get(quantity)
    return total_value

def cash_in_exogen_revenues(entity_data):
    accounts = entity_data.get("accounts")
    for account in accounts.nodes(data=True):
        account_data = account[-1]
        account_data["final_balance"] += account_data.get("exogen_revenue", 0)
#
# class Entity:
#     def __init__(self, **kargs):
#         self.__dict__.update(**kargs)
#
#
#     def get_id(self):
#         return self.__dict__.get("id", -1)
#
#     def __key(self):
#         return (self.get_id())
#
#     def __eq__(x, y):
#         return x.__key() == y.__key()
#
#     def __hash__(self):
#         return hash(self.__key())