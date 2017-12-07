import logging

import networkx as nx
import numpy as np
from scipy import sparse
from scipy.optimize import fmin_l_bfgs_b

from . import accountsModule
from . import entityModule
from . import transactionModule

logger = logging.getLogger(__name__)


def create_entities_network(entities_dict_list, accounts_dict_list, transaction_dict_list):
    """
    Create an entity network from list of entities, accounts and transaction
    :param entities_dict_list: list of entities dictionaries
    :param accounts_dict_list: list of account dictionaries
    :param transaction_dict_list: list of transactions dictionaries
    :return: networkx.MultiDiGraph
    """
    entities_network = EntitiesNetwork()
    add_entities_nodes(entities_network, entities_dict_list)
    account_id_to_entity_id_dict = add_accounts_nodes_to_entities(entities_network, accounts_dict_list)
    add_transactions_edges__between_entities(entities_network, transaction_dict_list, account_id_to_entity_id_dict)
    # compute a matrix representation of the network
    entities_network.update_network()
    return entities_network


def add_entities_nodes(entities_network, entities_dict_list):
    """
    create the entities nodes inside the entities_network
    :param entities_network:
    :param entities_dict_list:
    :return:
    """
    for entity_dict in entities_dict_list:
        entity_id = entity_dict.get("id")
        entities_network.add_entity(entity_id, entity_dict, accountsModule.create_accounts_digraph([]))


def add_accounts_nodes_to_entities(entities_network, accounts_dict_list):
    """
    add accounts nodes to entities contained in the entities_network
    :param entities_network:
    :param accounts_dict_list:
    :return: dictionary account_id --> owner entity id
    """
    account_id_to_entity_id_dict = dict()
    for account_data in accounts_dict_list:
        owner_entity_data = get_account_owner_entity_data(entities_network, account_data.get("owner_id"))
        if owner_entity_data is None:
            continue
        entityModule.add_account(owner_entity_data, account_data)
        account_id_to_entity_id_dict[account_data.get("id")] = owner_entity_data.get("id")
    return accounts_dict_list


def add_transactions_edges__between_entities(entities_network, transaction_dict_list, account_id_to_entity_id_dict):
    """
    add transactions between entities
    :param entities_network:
    :param transaction_dict_list:
    :param account_id_to_entity_id_dict:
    :return:
    """
    for transaction_to_add in transaction_dict_list:
        initiator_entity = get_entity_id_from_account_id(transaction_to_add.get("initiator_account"),
                                                         account_id_to_entity_id_dict)
        destinatary_entity = get_entity_id_from_account_id(transaction_to_add.get("destinatary_account"),
                                                           account_id_to_entity_id_dict)
        if initiator_entity is None or destinatary_entity is None:
            continue
        entities_network.add_transaction(initiator_entity, destinatary_entity, transaction_to_add)


def get_account_owner_entity_data(entities_network, owner_id):
    """
    get the data of an entity based on its id
    :param entities_network:
    :param owner_id:
    :return: dictionary of entity data
    """
    try:
        return entities_network.get_network().node[owner_id]
    except KeyError:
        logger.error("Unknown entity: {}".format(owner_id))
        return None


def get_entity_id_from_account_id(account_id, account_id_to_entity_id_dict):
    """
    retrieve the id of the entity from an unique account id
    :param account_id:
    :param account_id_to_entity_id_dict:  dictionary account id --> entity id
    :return: entity_id
    """
    entity_id = account_id_to_entity_id_dict.get(account_id, None)
    if account_id is None:
        logger.error("Account {} is not associated to any entity.".format(account_id))
    return entity_id


def solve_initial_network(entities_network):
    """
    computes transaction amount, revenues and final balance of accounts and taxes paid by the entities
    for the transaction ratio as defined by the user
    :param entities_network:
    :return:
    """
    compute_initial_taxes(entities_network)
    print("initial mean tax rate = {:.2f} %".format(100 * get_mean_tax_rate(entities_network)))


def solve_optimized_network(entities_network):
    """
    optimizes the transaction ratio to minimize total taxes
    then computes transaction amount, revenues and final balance of accounts and taxes paid by the entities
    for the transaction ratio as defined by the user
    :param entities_network:
    :return:
    """
    optimize_transfer_ratio(entities_network)
    print("optimized mean tax rate = {:.2f} %".format(100 * get_mean_tax_rate(entities_network)))


def compute_taxes(transfer_ratio, *args):
    """
    Solve the problem as a linear system
    :param transfer_ratio:
    :param args:
    :return:
    """
    logger.debug("transfer ratios = {}".format(str(transfer_ratio)))
    entities_network = args[0]
    # inner loop to evaluate the transfer ratios that should be computed from the state of the network
    computed_transfer_ratio = compute_computed_transfer_ratios(entities_network, transfer_ratio)
    set_transaction_transfer_ratio(entities_network, transfer_ratio, computed_transfer_ratio)
    compute_transactions_amounts(entities_network)
    compute_entities_revenue(entities_network)
    compute_entities_spendings(entities_network)
    compute_entities_final_accounts_balance(entities_network)
    compute_entities_taxes(entities_network, include_negative_cash_flow=True)
    total_tax_amount = get_total_taxes_amount(entities_network)
    return total_tax_amount


def compute_computed_transfer_ratios(entities_network, constant_transfer_ratios):
    """
    inner loop to compute transfer ratios that are computed from the state of the system.
    This is the case for the transfer ratios of the "THEIR" transaction.
    Iteratively converge to the value of the computed transfers ratios
    :param entities_network:
    :param constant_transfer_ratios:
    :return:
    """
    computed_transfer_ratios = np.array([0] * entities_network.number_of_computed_transfer_ratio)
    if not len(computed_transfer_ratios):
        return []
    res = 1
    under_relaxation = 0.5
    while res > 1e-6:
        set_transaction_transfer_ratio(entities_network, constant_transfer_ratios, computed_transfer_ratios)
        compute_transactions_amounts(entities_network)
        compute_entities_revenue(entities_network)
        compute_entities_spendings(entities_network)
        new_computed_transfer_ratios = under_relaxation * entities_network.get_computed_transfer_ratios() + \
                                       (1 - under_relaxation) * computed_transfer_ratios
        res = max(abs(new_computed_transfer_ratios - computed_transfer_ratios))
        computed_transfer_ratios = new_computed_transfer_ratios
    return computed_transfer_ratios


def optimize_transfer_ratio(entities_network):
    """
    launch the optiéization of the transfer ratio.
    :param entities_network:
    :return:
    """
    x0 = entities_network.get_constant_transfer_ratios()
    bounds = entities_network.get_transfer_ratio_bounds()
    fmin_l_bfgs_b(compute_taxes, x0, args=tuple([entities_network]), bounds=bounds, approx_grad=True, epsilon=1e-12)
    # re-compute taxes without negative taxes
    compute_entities_taxes(entities_network, include_negative_cash_flow=False)


def compute_initial_taxes(entities_network):
    """
    Launch the solver to compute initial taxes
    :param entities_network:
    :return:
    """
    x0 = entities_network.get_constant_transfer_ratios()
    compute_taxes(x0, entities_network)
    # re-compute taxes without negative taxes
    compute_entities_taxes(entities_network, include_negative_cash_flow=False)


def set_transaction_transfer_ratio(entities_network, constant_transfer_rates_list, computed_transfer_ratio_list):
    """
    Set new transfer ratio throughout the network
    :param entities_network:
    :param constant_transfer_rates_list: list of transfert ratio that will be imposed the "OUR" transaction
    :param computed_transfer_ratio_list: list of transfer ratio that were computed from the state of the network
    and that will be imposed to "THEIR" transactions
    :return:
    """
    transfer_ratios = []
    constant_transfer_rates = iter(constant_transfer_rates_list)
    computed_transfer_ratio = iter(computed_transfer_ratio_list)
    for transaction in entities_network.get_network().edges(data=True, keys=True):
        if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_OUR:
            transfer_ratios.append(next(constant_transfer_rates))
        elif transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_THEIR:
            transfer_ratios.append(next(computed_transfer_ratio))
    transfer_ratios_dict = dict(zip(entities_network.get_network().edges_iter(keys=True), transfer_ratios))
    nx.set_edge_attributes(entities_network.get_network(), "transfer_ratio", transfer_ratios_dict)


def compute_transactions_amounts(entities_network):
    """
    solve the (dual) linear problem M*X=V where:
    M = Identity matrix - transaction matrix
    X is the vector of transaction amounts
    V is the vector of exogen revenue for reference accounts group of each transaction * transactin transfer ratio
    For a desciption of the transaction matrix see " get_transaction_matrix"
    :param entities_network:
    :return: None
    """
    transfer_ratio_vector = np.array(
        list(nx.get_edge_attributes(entities_network.get_network(), "transfer_ratio").values()))
    transaction_matrix = entities_network.transaction_matrix.multiply(transfer_ratio_vector)
    identity_matrix = sparse.csr_matrix(sparse.identity(transaction_matrix.shape[0]))
    transaction_amount_matrix = sparse.csr_matrix.transpose(identity_matrix - transaction_matrix)
    exogen_transfer_share_vector = entities_network.exogen_transfers_vector * transfer_ratio_vector
    transaction_amounts = sparse.linalg.spsolve(transaction_amount_matrix, exogen_transfer_share_vector)
    transaction_amount_dict = dict(zip(entities_network.get_network().edges_iter(keys=True), transaction_amounts))
    nx.set_edge_attributes(entities_network.get_network(), "computed_amount", transaction_amount_dict)


def compute_entities_revenue(entities_network):
    """
    compute the revenue of each entity and each of its sub-accounts,
     taking into account its exogen revenue as well as internal transfers.
    set the value of the revenue to the entity data and account data (key "computed_revenue")
    :param entities_network:
    :return:
    """
    for entity_id in entities_network.get_network().nodes():
        inbound_transactions = entities_network.get_network().in_edges(entity_id, data=True)
        entity = entities_network.get_network().node[entity_id]
        entityModule.set_revenue(entity, inbound_transactions)


def compute_entities_spendings(entities_network):
    """
    compute the spending of each entity and each of its sub-accounts,
     taking into account its exogen spending as well as internal transfers.
    set the value of the spending to the entity data and account data (key "computed_spending")
    :param entities_network:
    :return:
    """
    for entity_id in entities_network.get_network().nodes():
        outbound_transactions = entities_network.get_network().out_edges(entity_id, data=True)
        entity = entities_network.get_network().node[entity_id]
        entityModule.set_spendings(entity, outbound_transactions)


def compute_entities_taxes(entities_network, include_negative_cash_flow=False):
    """
    compute the taxes of each entity, provided that its revenue was previously computed
    :param entities_network:
    :param include_negative_cash_flow: True or False. True means negative income leads to negative taxes
    :return:
    """
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        entityModule.compute_taxes(entity_data, include_negative_cash_flow=include_negative_cash_flow)


def get_total_taxes_amount(entities_network):
    """
    get the sum of the taxes paid by all entities
    :param entities_network:
    :return: total taxes amount (float)
    """
    total_taxes_amount = 0
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        total_taxes_amount += entity_data.get("paid_taxes", 0)
    logger.debug("total tax = {:.2f}".format(total_taxes_amount))
    return total_taxes_amount


def get_total_taxable_income(entities_network):
    """
    get the sum of the positive incomes of entities inside entities_network
    :param entities_network:
    :return:
    """
    total_taxable_income = 0
    for entity in entities_network.get_network().nodes(data=True):
        entity_data = entity[-1]
        total_taxable_income += entityModule.get_taxable_income(entity_data)
    return total_taxable_income


def get_mean_tax_rate(entities_network):
    """
    return the mean tax rate = total paid taxes / total taxable income
    :param entities_network:
    :return:
    """
    total_taxes_amount = get_total_taxes_amount(entities_network)
    total_taxable_income = get_total_taxable_income(entities_network)
    if total_taxable_income == 0:
        return 0
    return total_taxes_amount / total_taxable_income


def compute_entities_final_accounts_balance(entities_network):
    """
    compute the final balance of all accounts of entitiy network
    :param entities_network:
    :return:
    """
    entities_network.cash_in_exogen_revenues()
    entities_network.make_internal_transactions()


class EntitiesNetwork:
    """
    class representing an entitiy network
    the main attribute is _network (netwokx.MultiDiGraph())
    """
    def __init__(self):
        # multi directed graph representing the network
        self._network = nx.MultiDiGraph()
        # adjonction matrix, useful to solve the linear problem of transaction amounts
        self.transaction_matrix = None
        # vector of exogen amount, used by the linear equation solver
        self.exogen_transfers_vector = None
        #number of "OUR" transactions
        self.number_of_constant_transfer_ratio = 0
        # number of "THEIR" transactions
        self.number_of_computed_transfer_ratio = 0

    def add_entity(self, entity_id, entity_dict, accounts_digraph):
        """
        add one entity to the network
        :param entity_id:
        :param entity_dict:
        :param accounts_digraph:
        :return:
        """
        entity_dict["accounts"] = accounts_digraph
        self._network.add_node(entity_id, entity_dict)

    def get_network(self):
        """
        return the network object
        :return: networkx.MultiDiGraph
        """
        return self._network

    def add_transaction(self, initiator_entity, destinatary_entity, transaction_dict):
        """
        add a transaction edge
        :param initiator_entity: name of initiator entity
        :param destinatary_entity: name of destinatary entity
        :param transaction_dict:
        :return:
        """
        self._network.add_edge(initiator_entity, destinatary_entity, **transaction_dict)

    def update_network(self):
        """
        computes matrix representation of the network as well as constant caracteristics used by the solver
        :return:
        """
        self.transaction_matrix = self.get_transaction_matrix()
        self.exogen_transfers_vector = self.get_exogen_transfers_vector()
        self.number_of_constant_transfer_ratio = self.counts_constant_transfer_ratios()
        self.number_of_computed_transfer_ratio = len(self._network.edges()) - self.number_of_constant_transfer_ratio

    def counts_constant_transfer_ratios(self):
        """
        ge the number of "OUR" transactions
        :return: int
        """
        number_of_constant_transfer_ratios = 0
        transfer_ratio_calculation_dict = nx.get_edge_attributes(self._network, "transfer_ratio_calculation")
        for transfer_ratio_calculation in transfer_ratio_calculation_dict.values():
            if transfer_ratio_calculation == transactionModule.TRANSFER_RATIO_OUR:
                number_of_constant_transfer_ratios += 1
        return number_of_constant_transfer_ratios

    def get_account_balances_dict(self):
        """
        :return: dictionary. entity id --> sum of final balance of its accounts
        """
        account_balance_dict = dict()
        for entity in self._network.nodes(data=True):
            entity_id = entity[0]
            entity_data = entity[-1]
            account_balance_dict[entity_id] = entityModule.get_accounts_total(entity_data, "final_balance")
        return account_balance_dict

    def cash_in_exogen_revenues(self):
        """
        adds the exogen revenue of each accounts to its final balance
        :return:
        """
        for entity in self.get_network().nodes(data=True):
            entity_data = entity[-1]
            entityModule.cash_in_exogen_revenues(entity_data)

    def make_internal_transactions(self):
        """
        apply the effects of all internal transactions to the final balance of all accounts
        :return:
        """
        for entity_id in self._network.nodes():
            outbound_operations = self.get_network().out_edges(entity_id, data=True)
            inbound_operations = self.get_network().in_edges(entity_id, data=True)
            entity = self.get_network().node[entity_id]
            accounts = entity.get("accounts")
            transactionModule.make_transactions(accounts, outbound_operations, operation="debit")
            transactionModule.make_transactions(accounts, inbound_operations, operation="credit")

    def get_transaction_matrix(self):
        """
        the transaction matrix is the matrix in which each row and column represents a transaction
        the matrix component (i,j) is 1 if the transaction i is received by one of the reference accounts
        of the transaction j
        If the transfer mode of transaction j is based on the earning of the destinatary rather than the revenue of
        the initiator, then the component (i, j) is 1 if the transaction i is paid from one of the reference accounts
        of the transaction j
        :param :
        :return: nb_transaction * nb_transaction sparse csr matrix
        """
        rows = []
        for transaction in self.get_network().edges(data=True, keys=True):
            rows.append(self.get_transaction_matrix_row(transaction))
        return sparse.csr_matrix.transpose(sparse.vstack(rows))

    def get_transaction_matrix_row(self, reference_transaction):
        """
        return a row of the transaction matrix
        :param reference_transaction:
        :return: csr matrix
        """
        reference_transaction_data = reference_transaction[-1]
        reference_entity_id = transactionModule.get_reference_entity_id(reference_transaction)
        reference_entity_data = self._network.node[reference_entity_id]
        reference_accounts = transactionModule.get_reference_accounts(reference_entity_data, reference_transaction_data)
        row = np.zeros(len(self.get_network().edges()))
        for idx, transaction in enumerate(self.get_network().edges(data=True)):
            row[idx] = self.get_transaction_matrix_component(transaction, reference_entity_id, reference_accounts,
                                                             transfer_ratio_calculation=reference_transaction_data.get(
                                                                 "transfer_ratio_calculation"))
        return sparse.csr_matrix(row)

    @staticmethod
    def get_transaction_matrix_component(transaction, reference_entity_id, reference_accounts,
                                         transfer_ratio_calculation=transactionModule.TRANSFER_RATIO_OUR):
        """
        get a component of the transaction matrix
        :param transaction:
        :param reference_entity_id:
        :param reference_accounts:
        :param transfer_ratio_calculation:
        :return:
        """
        if transfer_ratio_calculation == transactionModule.TRANSFER_RATIO_THEIR:
            if transaction[0] == reference_entity_id and transaction[-1].get("initiator_account") in reference_accounts:
                return 1
            return 0
        if transaction[1] == reference_entity_id and transaction[-1].get("destinatary_account") in reference_accounts:
            return 1
        return 0

    def get_exogen_transfers_vector(self):
        """
        for a "OUR" transaction, exogen transfer is the total revenue of the reference accounts of the transaction
        for a "THEIR" transaction,  exogen transfer is the total spending of all the reference accounts of the transaction
        :return: numpy array of exogen transfer for all transactions
        """
        exogen_transfers = []
        for transaction in self._network.edges(data=True):
            reference_entity_id = transactionModule.get_reference_entity_id(transaction)
            reference_entity_data = self._network.node[reference_entity_id]
            total_exogen_transfer = entityModule.get_total_exogen_transfer(reference_entity_data, transaction[-1])
            exogen_transfers.append(total_exogen_transfer)
        return np.array(exogen_transfers)

    def get_constant_transfer_ratios(self):
        """
        get the transfer ratios of "OUR" transactions
        :return: array
        """
        computed_transfer_ratios = []
        transactions = self._network.edges(data=True)
        for transaction in transactions:
            if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_OUR:
                computed_transfer_ratios.append(transaction[-1].get("transfer_ratio"))
        return np.array(computed_transfer_ratios)

    def get_transfer_ratio_bounds(self):
        """
        get the bounds of the transafer ratios
        :return: array of two-tuples
        """
        transfer_ratio_bounds = []
        transactions = self._network.edges(data=True)
        for transaction in transactions:
            if transaction[-1].get("transfer_ratio_calculation") == transactionModule.TRANSFER_RATIO_OUR:
                transfer_ratio_bounds.append(transaction[-1].get("transfer_ratio_bounds"))
        return np.array(transfer_ratio_bounds)

    def get_computed_transfer_ratios(self):
        """
        compute and return the transfer ratios of all "THEIR" transactions
        :return: array
        """
        computed_transfer_ratios = []
        transfer_ratio_calculations = nx.get_edge_attributes(self._network, "transfer_ratio_calculation")
        for transaction, transfer_ratio_calculation in transfer_ratio_calculations.items():
            if transfer_ratio_calculation == transactionModule.TRANSFER_RATIO_OUR:
                continue
            computed_transfer_ratio = self.get_transaction_computed_transfer_ratio(transaction)
            computed_transfer_ratios.append(computed_transfer_ratio)
        return np.array(computed_transfer_ratios)

    def get_transaction_computed_transfer_ratio(self, transaction):
        """
        compute and return the transfert ratio of one "THEIR" transaction
        :param transaction:
        :return: float
        """
        initiator_entity_id = transaction[0]
        initiator_entity = self._network.node[initiator_entity_id]
        initiator_entity_revenue = initiator_entity.get("computed_revenue")
        initiator_outbound_operations = self.get_network().out_edges(initiator_entity_id, data=True, keys=True)
        outbound_entity_spendings = 0
        for initiator_outbound_operation in initiator_outbound_operations:
            accounts = transactionModule.get_reference_accounts(initiator_entity, initiator_outbound_operation[-1])
            destinatary_entity_data = self._network.node[initiator_outbound_operation[1]]
            outbound_entity_spendings += entityModule.get_accounts_total(destinatary_entity_data, "computed_spending",
                                                                         accounts=accounts)
        if outbound_entity_spendings != 0:
            return initiator_entity_revenue / outbound_entity_spendings
        return 1 / len(initiator_outbound_operations)
