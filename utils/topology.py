""" Script to write topology file """

import json
from anytree import AnyNode, find_by_attr, findall, RenderTree
from io import StringIO
#from cStringIO import StringIO

from utils import config


from mininet.topo import Topo 
from mininet.net import Mininet, CLI
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import output, warn
from mininet.term import makeTerm
from random import randint

import json
import sys
import time
import os
import re
import pwd

sys.path.append('..')


TIMEOUT=5

HOST_REGEX='\sh[0-9]+\[type=host'
SWITCH_REGEX='\ss[0-9]+\[type=switch'
LINK_REGEX='\s(h|s)[0-9]+ -> (h|s)[0-9]+'

class DotTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        self.dot_nodes = {}
        self.dot_links = []

    def add_host(self, line):
        host = self.parse_line(line)
        self.dot_nodes[host['name']] = self.addHost(host['name'], mac=host['mac'], ip=host['ip'])

    def add_switch(self, line):
        switch = self.parse_line(line)
        self.dot_nodes[switch['name']] = self.addSwitch(switch['name'], dpid=switch['id'])

    def add_link(self, line):
        tokens = self.parse_line(line)
        nodes = tuple(filter(None, re.split('[\-> ]',tokens['name'])))
        for link in self.dot_links:
            n1, n2 = link
            if n1 == nodes[1] and n2 == nodes[0]:
                return
        self.dot_links.append(nodes)

    def parse_line(self, line):
        result = {}
        tokens = list(filter(None, re.split('[\[\],;]',line.strip())))
        result['name'] = tokens[0]
        for token in tokens[1:]:
            key, value = token.split('=')
            result[key] = value.strip('\"')
        return result

    def import_dot(self, fname):
        f = open(fname)
        matches = {
            'host':HOST_REGEX,
            'switch':SWITCH_REGEX,
            'link':LINK_REGEX
        }
        for l in f:
            for m in matches:
                pattern = re.compile(matches[m])
                if pattern.match(l):
                    if m == 'host':
                        self.add_host(l)
                    elif m == 'switch':
                        self.add_switch(l)
                    elif m == 'link':
                        self.add_link(l)

        for link in self.dot_links:
            n1, n2 = link
            self.addLink(n1, n2)

def start_mininet():
    controller = RemoteController('c0', ip='127.0.0.1', port=6633)
    print("asasasasasa")
    topo=DotTopo()
    topo.import_dot('../res/topology.dot')
    print("sasxass")
    net = Mininet(topo=topo, controller=controller, link=TCLink)
   
    controller.start()
    net.start()

    # while True:
    random_host1 = net.get('h%d'%randint(1,160))
    random_host2 = net.get('h%d'%randint(1,160))

    makeTerm(random_host1, title='Iperf Server', cmd='iperf -s')
    makeTerm(random_host2, title='Iperf Client', cmd='iperf -c '+random_host1.IP())

    file = open(config.TC_COMMANDS_PATH)

    start_time = time.time()
    rules_tc = json.loads(file.read())
    for rule_ip in rules_tc:
        print(rule_ip)
        for i in range(1,160):
            host = net.get('h{}'.format(i))
            if host.IP() == rule_ip:
                print(rule_ip)
                break
        for rule in rules_tc:
            makeTerm(host, title='Commands', cmd=rule)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    return elapsed_time



IP_COUNTER = 2
SUBNET_ID = 1
TOPOLOGY = {}


def make_link(source, target, capacity, src_id=None, dst_id=None, src_port=0, dst_port=0):
    """ Creates link NetJSON format """
    return {
        "source": source,
        "source_id": src_id,
        "target": target,
        "target_id": dst_id,
        "source_port": src_port,
        "target_port": dst_port,
        "cost": 1.000,
        "properties": {
            "capacity": [capacity, 'mbps']
        }
    }


def make_node(node_type, func, idx, label, index=0):
    """ Creates node in NetJSON format """
    global IP_COUNTER, SUBNET_ID
    ip = "172.16.{}.{}".format(SUBNET_ID, IP_COUNTER)
    IP_COUNTER += 1
    if IP_COUNTER == 254:
        IP_COUNTER = 2
        SUBNET_ID += 1

    return {
        "id": ip,
        "label": "{} {} {}".format(node_type, func, idx),
        "properties": {
            "hostname": "{}{}.cs.edu".format(func, idx),
            "name": node_type[0] + str(index),
            "handles": [
                node_type,
                func,
                label
            ]
        }
    }


def write_dot():
    """ Creates campus topology in Dot format """
    global SUBNET_ID

    str_writer = StringIO()

    str_writer.write('digraph g1 {\n')

    nodes = {}
    ports = {}
    for i in range(1, 24):
        ports['s' + str(i)] = 1
    hosts = []
    switches = []
    links = []
    c = 1
    s = 1
    core_switch = make_node("switch", "core", 1, "core", 1)
    nodes['s1'] = core_switch
    switches.append(core_switch)
    for i in range(1, 3):
        s += 1
        core_switch = make_node("switch", "core", i, "core", s)
        nodes[core_switch['properties']['name']] = core_switch
        switches.append(core_switch)
        links.append(make_link("19.16.1.1", core_switch["id"], 10000, "s1", core_switch['properties']
                               ['name'], ports['s1'], ports[core_switch['properties']['name']]))
        links.append(make_link(core_switch["id"], "19.16.1.1", 10000, core_switch['properties']
                               ['name'], "s1", ports[core_switch['properties']['name']], ports['s1']))
        ports['s1'] += 1
        ports[core_switch['properties']['name']] += 1

        for j in range(1, 3):
            s += 1
            aggr_switch = make_node("switch", "aggr", j, "aggregation", s)
            nodes[aggr_switch['properties']['name']] = aggr_switch
            switches.append(aggr_switch)
            links.append(make_link(core_switch["id"], aggr_switch["id"], 1000, core_switch['properties']['name'],
                                   aggr_switch['properties']['name'], ports[core_switch['properties']['name']], ports[aggr_switch['properties']['name']]))
            links.append(make_link(aggr_switch["id"], core_switch["id"], 1000, aggr_switch['properties']['name'],
                                   core_switch['properties']['name'], ports[aggr_switch['properties']['name']], ports[core_switch['properties']['name']]))
            ports[core_switch['properties']['name']] += 1
            ports[aggr_switch['properties']['name']] += 1

            for k in range(1, 5):
                s += 1
                SUBNET_ID += k
                edge_switch = make_node("switch", "edge", k, config.DATASET_GROUPS[k - 1], s)
                nodes[edge_switch['properties']['name']] = edge_switch
                switches.append(edge_switch)
                links.append(make_link(aggr_switch["id"], edge_switch["id"], 100, aggr_switch['properties']['name'],
                                       edge_switch['properties']['name'], ports[aggr_switch['properties']['name']], ports[edge_switch['properties']['name']]))
                links.append(make_link(edge_switch["id"], aggr_switch["id"], 100, edge_switch['properties']['name'],
                                       aggr_switch['properties']['name'], ports[edge_switch['properties']['name']], ports[aggr_switch['properties']['name']]))
                ports[aggr_switch['properties']['name']] += 1
                ports[edge_switch['properties']['name']] += 1
                for l in range(1, 11):
                    host = make_node("host", "h", c, config.DATASET_GROUPS[k - 1], c)
                    nodes[host['properties']['name']] = host
                    hosts.append(host)
                    links.append(make_link(edge_switch["id"], host["id"], 100, edge_switch['properties']
                                           ['name'], host['properties']['name'], ports[edge_switch['properties']['name']]))
                    links.append(make_link(host["id"], edge_switch["id"], 100, host['properties']['name'],
                                           edge_switch['properties']['name'], 0, ports[edge_switch['properties']['name']]))
                    ports[edge_switch['properties']['name']] += 1
                    c += 1

    for middlebox in config.DATASET_MIDDLEBOXES:
        MAC_MASK = '00:00:00:00:%02d:%02d'
        m = make_node("host", middlebox, 1, middlebox, c)
        mac = MAC_MASK % tuple(map(lambda x: int(x) % 100, m['id'].split('.')[-2:]))
        m['properties']['name'] = middlebox
        middlebox_name = middlebox.replace('-', '')
        links.append(make_link("19.16.1.1", m["id"], 100, "s1", middlebox_name, ports["s1"]))
        links.append(make_link(m["id"], "19.16.1.1", 100, middlebox_name, "s1", 0, ports["s1"]))
        ports["s1"] += 1

        str_writer.write('\t{}[type=host,ip="{}",mac="{}"];\n'.format(middlebox_name, m['id'], mac))

    for h in hosts:
        MAC_MASK = '00:00:00:00:%02d:%02d'
        mac = MAC_MASK % tuple(map(lambda x: int(x) % 100, h['id'].split('.')[-2:]))
        hname = h['properties']['hostname'].split('.')[0]
        str_writer.write('\t{}[type=host,ip="{}",mac="{}"];\n'.format(hname, h['id'], mac))

    for i in range(len(switches)):
        id = switches[i]['properties']['name']
        index = id[1:]
        ip = switches[i]['id']
        str_writer.write('\t{}[type=switch,ip="{}",id={}];\n'.format(id, ip, index))

    for l in links:
        src_id = l['source_id']
        dst_id = l['target_id']
        str_writer.write('\t{} -> {} [src_port={}, dst_port={}, cost=1];\n'.format(src_id,
                                                                                   dst_id, l['source_port'], l['target_port']))

    str_writer.write('}')

    with open(config.TOPOLOGY_DOT_PATH, 'w') as topology_file:
        topology_file.write(str_writer.getvalue())


def write(format='json'):
    """ Creates campus topology in NetJSON or DOT format """
    if(format == 'dot'):
        return write_dot()

    global SUBNET_ID

    topology = {
        "type": "NetworkGraph",
        "protocol": "olsr",
        "version": "0.6.6",
        "revision": "5031a799fcbe17f61d57e387bc3806de",
        "metric": "etx",
        "router_id": "172.16.1.1",
        "label": "Campus Network",
        "nodes": [
            {
                "id": "19.16.1.1",
                "label": "Gateway",
                "properties": {
                    "hostname": "gateway.rs.edu",
                    "handles": [
                        "gateway",
                        "internet"
                    ]
                }
            }
        ],
        "links": []
    }

    nodes = []
    links = []

    for i in range(1, 3):
        core_switch = make_node("switch", "core", i, "core")
        nodes.append(core_switch)
        links.append(make_link("19.16.1.1", core_switch["id"], 10000))
        for j in range(1, 3):
            aggr_switch = make_node("switch", "aggr", j, "aggregation")
            nodes.append(aggr_switch)
            links.append(make_link(core_switch["id"], aggr_switch["id"], 1000))

            for k in range(1, 5):
                SUBNET_ID += k
                edge_switch = make_node("switch", "edge", k, config.DATASET_GROUPS[k - 1])
                nodes.append(edge_switch)
                links.append(make_link(aggr_switch["id"], edge_switch["id"], 100))

                for l in range(1, 11):
                    host = make_node("host", "physical", l, config.DATASET_GROUPS[k - 1])
                    nodes.append(host)
                    links.append(make_link(edge_switch["id"], host["id"], 100))

    topology["nodes"] = topology["nodes"] + nodes
    topology["links"] = links

    with open(config.TOPOLOGY_PATH, 'w') as topology_file:
        json.dump(topology, topology_file, indent=4, sort_keys=True)


def read():
    """ Loads topology from file """
    global TOPOLOGY
    if TOPOLOGY:
        return TOPOLOGY

    TOPOLOGY = {}
    with open(config.TOPOLOGY_PATH) as topology_file:
        topology = json.load(topology_file)
    return topology


def get_path_capacity(source, target):
    """ given an origin and a destination, get bandwidth capacity """
    node_tree = get_node_tree()
    source_node = find_by_attr(node_tree, name='id', value=source)
    target_node = find_by_attr(node_tree, name='id', value=target)

    return min(source_node.capacity, target_node.capacity)


def get_common_path(path_a, path_b):
    """ given two paths, return common path source and target """

    node_tree = get_node_tree()
    source_a = find_by_attr(node_tree, name='id', value=path_a[0])
    target_a = find_by_attr(node_tree, name='id', value=path_a[1])
    source_b = find_by_attr(node_tree, name='id', value=path_b[0])
    target_b = find_by_attr(node_tree, name='id', value=path_b[1])

    source = source_a if source_a == source_b else None
    target = None

    for node_a, node_b in zip(target_a.path, target_b.path):
        if node_a == node_b:
            target = node_a
        else:
            break

    return source.id, target.id


def get_common_path_list(path_a, path_b):
    """ given two paths, return common path source and target """

    node_tree = get_node_tree()
    source_a = find_by_attr(node_tree, name='id', value=path_a[0])
    target_a = find_by_attr(node_tree, name='id', value=path_a[1])
    source_b = find_by_attr(node_tree, name='id', value=path_b[0])
    target_b = find_by_attr(node_tree, name='id', value=path_b[1])

    source = source_a if source_a == source_b else None
    common_path = [source]

    for node_a, node_b in zip(target_a.path, target_b.path):
        if node_a == node_b:
            common_path.append(node_a)
        else:
            break

    return common_path


def get_group_ip(group):
    """ given a group, get the ip of the group switch """
    root = get_node_tree()
    group_node = findall(root, lambda node: next((True for x in node.properties['handles'] if x == group), False))[0]
    return group_node.id if group_node else None


def get_service(service):
    """ given a service, get the ip of the group switch """
    # do something
    print(service)
    return (["34.234.59.120", "34.234.59.11"], 'tcp', '8080')


def get_traffic_flow(traffic):
    """ given a traffic, get the ip of the group switch """
    # do something
    print(traffic)
    return ('tcp', '5060')


def is_ancestor(parent, child):
    """ given two nodes, check if one is ancestor of the other """
    root = get_node_tree()
    child_node = find_by_attr(root, name='id', value=child)
    ancestry = False
    for node in child_node.ancestors:
        ancestry = node.id == parent or ancestry

    return ancestry


def is_descendent(parent, child):
    """ given two nodes, check if one is ancestor of the other """
    root = get_node_tree()
    parent_node = find_by_attr(root, name='id', value=parent)
    decendency = False
    for node in parent_node.descendants:
        decendency = node.id == child or decendency

    return decendency


def is_bandwidth_available(source, target, bandwidth, constraint):
    """ checks if given bandwidth is available in given path """
    path_capacity = get_path_capacity(source, target)
    return path_capacity >= bandwidth if constraint == 'min' else bandwidth >= path_capacity


def get_node_tree():
    """ reads nodes from topology and builds tree """
    topology = read()
    tree_nodes = []
    for link in topology['links']:
        parent_ip = link['source']
        child_ip = link['target']
        link_capacity = link['properties']['capacity'][0]

        parent = next((x for x in tree_nodes if x.id == parent_ip), None)
        if not parent:
            parent_node = next((x for x in topology['nodes'] if x['id'] == parent_ip), None)
            parent = AnyNode(id=parent_node['id'], label=parent_node['label'],
                             properties=parent_node['properties'], capacity=float("inf"))
            tree_nodes.append(parent)

        child = next((x for x in tree_nodes if x.id == child_ip), None)
        if not child:
            child_node = next((x for x in topology['nodes'] if x['id'] == child_ip), None)
            child = AnyNode(id=child_node['id'], parent=parent, label=child_node['label'],
                            properties=child_node['properties'], capacity=min(parent.capacity, link_capacity))
            tree_nodes.append(child)
        child.parent = parent

    root = next((x for x in tree_nodes if x.parent is None), None)

    #with open(config.TOPOLOGY_PATH + '.txt', 'w') as topology_file:
    #     topology_file.write(u' '.join(RenderTree(root).by_attr('id')).encode('utf-8'))

    return root


if __name__ == "__main__":
    deploy_time = start_mininet()
    print("Deploy time: ", deploy_time)
    write(format='dot')
