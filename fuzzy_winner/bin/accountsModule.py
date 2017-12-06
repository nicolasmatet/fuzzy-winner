import networkx as nx


def get_account_dict(account_id, owner_entity_id, balance, exogen_revenue, exogen_spending):
    return {"owner_id": str(owner_entity_id).strip().upper(), "id": str(account_id).strip().upper(),
            "initial_balance": float(balance),
            "final_balance": float(balance),
            "exogen_revenue": float(exogen_revenue),
            "exogen_spending": max(1e-12, float(exogen_spending))}


def create_accounts_digraph(account_dict_list):
    account_digraph = nx.MultiDiGraph()
    for account_dict in account_dict_list:
        account_digraph.add_node(account_dict.get("id"), **account_dict)
    return account_digraph


def get_account_labels(accounts_digraph):
    initial_balance = nx.get_node_attributes(accounts_digraph, "initial_balance")
    final_balance = nx.get_node_attributes(accounts_digraph, "final_balance")
    id_dict = nx.get_node_attributes(accounts_digraph, "id")
    labels = ["{}\n"
              "initial balance {:.3f}\n"
              "final balance {:.3f}\n".format(node_id, initial_balance, final_balance)
              for node_id, initial_balance, final_balance
              in zip(id_dict.values(),
                     initial_balance.values(),
                     final_balance.values())]
    node_labels = dict(zip(accounts_digraph.nodes(), labels))
    return node_labels


def get_account_tooltip(accounts_digraph):
    exogen_revenue_dict = nx.get_node_attributes(accounts_digraph, "exogen_revenue")
    exogen_spending_dict = nx.get_node_attributes(accounts_digraph, "exogen_spending")
    labels = ["exogen revenue {:.2f}   /   "
              "exogen spendings {:.2f}".format(exogen_revenue, exogen_spending)
              for exogen_revenue, exogen_spending
              in zip(exogen_revenue_dict.values(),
                     exogen_spending_dict.values())]
    node_labels = dict(zip(accounts_digraph.nodes(), labels))
    return node_labels
