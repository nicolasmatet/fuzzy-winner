import networkx as nx


def get_account_dict(owner_entity_id, account_id, balance, exogen_revenue):
    return {"owner_id": owner_entity_id, "id": account_id,
            "initial_balance": balance,
            "final_balance": balance,
            "exogen_revenue": exogen_revenue}


def create_accounts_digraph(account_dict_list):
    account_digraph = nx.MultiDiGraph()
    for account_dict in account_dict_list:
        account_digraph.add_node(account_dict.get("id"), **account_dict)
    return account_digraph


