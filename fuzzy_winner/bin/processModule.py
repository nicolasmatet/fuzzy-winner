import networkx as nx
import pydotplus

from . import accountsModule, entityModule, transactionModule, entitiesNetworkModule
from .readerModule import read_accounting_book

'''
This module is the entry point to the transaction viewer/optimizer
Front-end can call either 
compute_transactions_network to simply compute the final state of the accounts 
or
optimize_transactions_network to optimize the transaction ratios
'''

def compute_transactions_network(file):
    '''
    From the given entity network, compute transaction amounts, accounts balance and taxes.
    :param file: an excel (.xlsx) file (accounting book) defining the entities, transactions and accounts.
    See the documentation inside the excel file to know how to format it
    :return: DOT representation of the entities graph
    '''
    entities_dict_list, accounts_dict_list, transaction_dict_list = read_accounting_book(file)
    entities_network = entitiesNetworkModule.create_entities_network(
        entities_dict_list, accounts_dict_list, transaction_dict_list)
    entitiesNetworkModule.solve_initial_network(entities_network)
    graph_title = "Initial mean tax rate = {:.2f} %". \
        format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network))
    return get_dot_data(entities_network, graph_title=graph_title)


def optimize_transactions_network(file):
    """
    Optimize the transaction transfer ratios to minize taxes for the given entity network
    :param file: an excel (.xlsx) file (accounting book) defining the entities, transactions and accounts.
    See the documentation inside the excel file to know how to format it
    :return: DOT representation of the entities graph
    """
    entities_dict_list, accounts_dict_list, transaction_dict_list = read_accounting_book(file)
    entities_network = entitiesNetworkModule.create_entities_network(
        entities_dict_list, accounts_dict_list, transaction_dict_list)
    entitiesNetworkModule.solve_optimized_network(entities_network)
    graph_title = "Optimized mean tax rate = {:.2f} %". \
        format(100 * entitiesNetworkModule.get_mean_tax_rate(entities_network))
    return get_dot_data(entities_network, graph_title=graph_title)


def get_dot_data(entities_network, graph_title=""):
    """
    construct the DOT representation of the entities network
    :param entities_network:
    :param graph_title: title of the graph
    :return: DOT format graph
    """
    format_graph(entities_network)
    # convert the networkx graph to pydot
    main_graph_pydot = nx.nx_pydot.to_pydot(entities_network.get_network())
    # set the graph title
    main_graph_pydot.obj_dict['attributes']['label'] = graph_title
    main_graph_pydot.obj_dict['attributes']['labelloc'] = "t"
    """
    add nodes representing the accounts directly to the DOT representation.
    TODO: instead of adding accounts nodes to DOT graph, add them directly to the networkx graph and find a way to cluster them in networkx format
    """
    add_accounts_nodes_to_DOT_graph(entities_network, main_graph_pydot)
    return main_graph_pydot


def add_accounts_nodes_to_DOT_graph(entities_network, main_graph_pydot):
    # for each entity, get a sub-graph representing the entity and its accounts and add it the the DOT graph
    for node in entities_network.get_network().nodes(data=True):
        account_cluster = get_accounts_cluster(node)
        main_graph_pydot.add_subgraph(account_cluster)

def get_accounts_cluster(entity):
    """
    get a sub-graph representing the entity and its accounts.
    :param entity: central entity of the subgraph
    :return: subgraph
    """
    accounts = entity[-1].get("accounts")
    account_labels = accountsModule.get_account_labels(accounts)
    account_tooltips = accountsModule.get_account_tooltip(accounts)
    entity_id = entity[0]
    account_cluster = pydotplus.Subgraph(name='cluster_' + str(entity[0]))
    for account in accounts.nodes(data=True):
        set_account_to_entity_edge(account_cluster, entity_id, account, account_labels, account_tooltips)
    return account_cluster


def set_account_to_entity_edge(account_cluster, entity_id, account, accounts_labels, accounts_toooltips):
    """
    for a given account and a central entity, create a node representing the account and an edge liking it to the central entity
    :param account_cluster: subgraph to which this new edge belongs
    :param entity_id: id of the central entity
    :param account: account that is represented by the node we are now adding
    :param accounts_labels: dictionnary account id --> account display text
    :param accounts_toooltips: dictionnary account id --> account tooltip
    :return: None
    """
    account_node = pydotplus.Node(accounts_labels.get(account[0]), tooltip=accounts_toooltips.get(account[0]))
    account_node.add_style("rectangle")
    account_cluster.add_node(account_node)
    account_to_entity_edge = pydotplus.Edge(pydotplus.Node(entity_id), account_node, arrowhead="none", style="dotted")
    account_cluster.add_edge(account_to_entity_edge)


def format_graph(entities_network):
    """
    Set some attributes of the networkx format graph that will be used during conversion to DOT format
    :param entities_network:
    :return: None
    """
    # entities nodes style
    nx.set_node_attributes(entities_network.get_network(), "fillcolor", "lightgrey")
    nx.set_node_attributes(entities_network.get_network(), "color", "lightblue")
    nx.set_node_attributes(entities_network.get_network(), "style", "filled")
    # entites nodes display text and tooltip
    edge_label_dict = transactionModule.get_transactions_labels(entities_network)
    edge_tooltip_dict = transactionModule.get_transactions_tooltips(entities_network)
    nx.set_node_attributes(entities_network.get_network(), "label", node_label_dict)
    nx.set_edge_attributes(entities_network.get_network(), "label", edge_label_dict)
    # transaction edges text and tooltip
    node_label_dict = entityModule.get_entities_labels(entities_network)
    node_tooltip_dict = entityModule.get_entities_tooltips(entities_network)
    nx.set_node_attributes(entities_network.get_network(), "tooltip", node_tooltip_dict)
    nx.set_edge_attributes(entities_network.get_network(), "labeltooltip", edge_tooltip_dict)
