import networkx as nx
import pydotplus

from . import accountsModule, entityModule, transactionModule, entitiesNetworkModule
from .readerModule import read_accounting_book


def compute_transactions_network(file):
    entities_dict_list, accounts_dict_list, transaction_dict_list = read_accounting_book(file)
    entities_network = entitiesNetworkModule.create_entities_network(
        entities_dict_list, accounts_dict_list, transaction_dict_list)
    entitiesNetworkModule.solve_initial_network(entities_network)
    graph_title = "Initial mean tax rate = {:.2f} %". \
        format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network))
    return get_dot_data(entities_network, graph_title=graph_title)


def optimize_transactions_network(file):
    entities_dict_list, accounts_dict_list, transaction_dict_list = read_accounting_book(file)
    entities_network = entitiesNetworkModule.create_entities_network(
        entities_dict_list, accounts_dict_list, transaction_dict_list)
    entitiesNetworkModule.solve_optimized_network(entities_network)
    graph_title = "Optimized mean tax rate = {:.2f} %". \
        format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network))
    return get_dot_data(entities_network, graph_title=graph_title)


def get_dot_data(entities_network, graph_title=""):
    format_graph(entities_network)
    main_graph_pydot = nx.nx_pydot.to_pydot(entities_network.get_network())
    main_graph_pydot.obj_dict['attributes']['label'] = graph_title
    main_graph_pydot.obj_dict['attributes']['labelloc'] = "t"

    for node in entities_network.get_network().nodes(data=True):
        account_cluster = get_accounts_cluster(node)
        main_graph_pydot.add_subgraph(account_cluster)
    return main_graph_pydot


def get_accounts_cluster(entity):
    accounts = entity[-1].get("accounts")
    account_labels = accountsModule.get_account_labels(accounts)
    account_tooltips = accountsModule.get_account_tooltip(accounts)
    entity_id = entity[0]
    account_cluster = pydotplus.Subgraph(name='cluster_' + str(entity[0]))
    for account in accounts.nodes(data=True):
        set_account_to_entity_edge(account_cluster, entity_id, account, account_labels, account_tooltips)
    return account_cluster


def set_account_to_entity_edge(account_cluster, entity_id, account, accounts_labels, accounts_toooltips):
    account_node = pydotplus.Node(accounts_labels.get(account[0]), tooltip=accounts_toooltips.get(account[0]))
    account_node.add_style("rectangle")
    account_cluster.add_node(account_node)
    account_to_entity_edge = pydotplus.Edge(pydotplus.Node(entity_id), account_node, arrowhead="none", style="dotted")
    account_cluster.add_edge(account_to_entity_edge)


def format_graph(entities_network):
    edge_label_dict = transactionModule.get_transactions_labels(entities_network)
    edge_tooltip_dict = transactionModule.get_transactions_tooltips(entities_network)
    node_label_dict = entityModule.get_entities_labels(entities_network)
    node_tooltip_dict = entityModule.get_entities_tooltips(entities_network)
    nx.set_node_attributes(entities_network.get_network(), "fillcolor", "lightgrey")
    nx.set_node_attributes(entities_network.get_network(), "color", "lightblue")
    nx.set_node_attributes(entities_network.get_network(), "style", "filled")
    nx.set_node_attributes(entities_network.get_network(), "label", node_label_dict)
    nx.set_edge_attributes(entities_network.get_network(), "label", edge_label_dict)
    nx.set_node_attributes(entities_network.get_network(), "tooltip", node_tooltip_dict)
    nx.set_edge_attributes(entities_network.get_network(), "labeltooltip", edge_tooltip_dict)
