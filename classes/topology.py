from typing import List

from classes.controller_methods import ControllerMethods

class Topology():

    def __init__(self):
        self.nodes = {}
        self.controllers: List[ControllerMethods] = []

    def print_nodes(self) -> None:
        for key, value in self.nodes.items():
            print(key, ": ", value, end="\n\n")

    def add_controller(self, cm: ControllerMethods):
        self.controllers.append(cm)

    def make_network_graph(self) -> None:
        for controller in self.controllers:
            controller.map_topology(self.nodes)