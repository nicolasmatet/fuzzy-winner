import networkx as nx
import pydotplus

from . import accountsModule
from . import entitiesNetworkModule
from . import transactionModule
from .entitiesNetworkModule import solve_optimized_network, solve_initial_network, create_entities_network, \
    get_drawing_node_labels
from .readerModule import read_accounting_book


def compute_transactions_network(file):
    entities_dict_list, accounts_dict_list, transaction_dict_list = read_accounting_book(file)
    entities_network = create_entities_network(entities_dict_list, accounts_dict_list, transaction_dict_list)
    solve_initial_network(entities_network)
    graph_title = "Initial mean tax rate = {:.2f} %". \
        format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network))
    return get_dot_data(entities_network, graph_title=graph_title)


def optimize_transactions_network(file):
    entities_dict_list, accounts_dict_list, transaction_dict_list = read_accounting_book(file)
    entities_network = create_entities_network(entities_dict_list, accounts_dict_list, transaction_dict_list)
    solve_optimized_network(entities_network)
    graph_title = "Optimized mean tax rate = {:.2f} %". \
        format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network))
    return get_dot_data(entities_network, graph_title=graph_title)


def get_dot_data(entities_network, graph_title=""):
    format_graph(entities_network)
    main_graph_pydot = nx.nx_pydot.to_pydot(entities_network.get_network())
    main_graph_pydot.obj_dict['attributes']['label'] = graph_title
    for node in entities_network.get_network().nodes(data=True):
        account_cluster = get_accounts_cluster(node)
        main_graph_pydot.add_subgraph(account_cluster)
    return main_graph_pydot


def get_accounts_cluster(node):
    accounts = node[-1].get("accounts")
    account_labels = accountsModule.get_account_labels(accounts)
    print(account_labels)
    main_node_id = node[0]
    account_cluster = pydotplus.Cluster(name='cluster_' + str(node[0]))
    for account in accounts.nodes(data=True):
        account_node = pydotplus.Node(str(account_labels.get(account[0])))
        e = pydotplus.Edge(pydotplus.Node(main_node_id), account_node, arrowhead="none", style="dotted")
        account_cluster.add_edge(e)
    return account_cluster


def format_graph(entities_network):
    tax_rate_dict = nx.get_node_attributes(entities_network.get_network(), "tax_rate")
    edge_label_dict = transactionModule.get_transactions_labels(entities_network)
    node_label_dict = get_drawing_node_labels(entities_network)
    nx.set_node_attributes(entities_network.get_network(), "fillcolor", "lightgrey")
    nx.set_node_attributes(entities_network.get_network(), "color", "lightblue")
    nx.set_node_attributes(entities_network.get_network(), "style", "filled")
    nx.set_node_attributes(entities_network.get_network(), "label", node_label_dict)
    nx.set_edge_attributes(entities_network.get_network(), "label", edge_label_dict)
    nx.set_node_attributes(entities_network.get_network(), "tooltip", tax_rate_dict)
