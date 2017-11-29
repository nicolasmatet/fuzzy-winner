import networkx as nx
import numpy as np



class EntitiesNetwork:
    def __init__(self):
        self._network =  nx.MultiDiGraph()

    def add_entity(self,entity_id, entity_object):
        self._network.add_node(entity_id, **entity_object.__dict__)

    def get_network(self):
        return self._network

    def add_transaction(self,destinatary_entity, initiator_entity,  transaction_dict):
        self._network.add_edge(destinatary_entity, initiator_entity, **transaction_dict)

    def get_exogen_revenue_vector(self):
        return np.array(list(nx.get_node_attributes(self._network, 'exogen_revenue').values()))
