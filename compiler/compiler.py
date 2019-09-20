""" Nile compiler """
import time

from parser import parse
from deployer import merlin as merlin_deployer
from manager import topology, storage


def to_sonata(op_targets):
    """ Given parsed operation targets, builds a SONATA-NFV intent """
    sonata_intent = ''

    middleboxes = []
    src_targets = []
    dest_targets = []

    ip = 2
    # creating middleboxes
    for mb in middleboxes:
        mb_start = 'firewall' if mb == 'firewall' else 'snort'  # support only firewall and ids middleboxes
        mb_start_cmd = '"./start_{}.sh 100 100 100 100 \'128KB\' 0 &"'.format(mb_start)
        mb_sh = 'echo {}\nvim-emu compute start -d vnfs_dc -n {} -i rjpfitscher/genic-vnf --net "(id=input,ip=10.0.0.{}0/24),(id=output,ip=10.0.0.{}1/24)" -c {}\n'.format(
            mb, mb, ip, ip, mb_start_cmd)
        ip += 1
        sonata_intent += mb_sh

    # chaining middleboxes
    for idx, mb in enumerate(middleboxes):
        if idx == 0:
            src = src_targets[0]
            src_sh = 'echo {}\nvim-emu network add -b -src {}:client-eth0 -dst {}:input\n'.format(src + '-' + mb, src, mb)
            sonata_intent += src_sh
        elif idx == len(middleboxes) - 1:
            dest = dest_targets[0]
            dest_sh = 'echo {}\nvim-emu network add -b -src {}:output -dst {}:server-eth0\n'.format(mb + '-' + dest, mb, dest)
            sonata_intent += dest_sh

        if idx != len(middleboxes) - 1:
            next_mb = middleboxes[idx + 1]
            chain_mb_sh = 'echo {}\nvim-emu network add -b -src {}:output -dst {}:input\n'.format(mb + '-' + next_mb, mb, next_mb)
            sonata_intent += chain_mb_sh

    return sonata_intent


def to_merlin(op_targets):
    """ Given parsed operation targets, builds a Merlin intent """
    merlin_intent = ""
    origin_ip, destination_ip = "", ""
    targets_ips = []
    src_services = []
    dst_services = []
    traffics = []
    protocols = []
    middleboxes = []
    rates = []

    if 'origin' in op_targets:
        origin = op_targets['origin']
        if origin['function'] == 'endpoint':
            origin_ip = origin['value'].replace("('", "").replace("')", "")
        else:  # service
            src_services.append(topology.get_service(origin['value'].replace("('", "").replace("')", "")))

    if 'destination' in op_targets:
        destination = op_targets['destination']
        if destination['function'] == 'endpoint':
            destination_ip = destination['value'].replace("('", "").replace("')", "")
        else:  # service
            dst_services.append(topology.get_service(destination['value'].replace("('", "").replace("')", "")))

    if 'targets' in op_targets:
        for target in op_targets['targets']:
            if target['function'] == 'endpoint':
                targets_ips.append(target['value'].replace("('", "").replace("')", ""))
            elif target['function'] == 'group':
                targets_ips.append(topology.get_group_ip(target['value'].replace("('", "").replace("')", "")))
            elif target['function'] == 'service':
                src_services.append(topology.get_service(target['value'].replace("('", "").replace("')", "")))
            elif target['function'] == 'traffic':
                traffics.append(topology.get_traffic_flow(target['value'].replace("('", "").replace("')", "")))

    for op in op_targets['operations']:
        if op['type'] == 'set':
            if op['function'] == 'bandwidth':
                params = op['value'].replace("('", "").replace("')", "").split(',')
                rates.append(params)
            else:
                middleboxes.append('quota')
        elif op['type'] == 'add':
            param = op['value'].replace("('", "").replace("')", "")
            middleboxes.append(param)
        elif op['type'] == 'allow':
            if op['function'] == 'protocol':
                param = op['value'].replace("('", "").replace("')", "")
                protocols.append(param)
            elif op['function'] == 'traffic':
                middleboxes.append('quota')
            elif op['function'] == 'service':
                src_services.append(topology.get_service(op['value'].replace("('", "").replace("')", "")))

    merlin_path = ""
    if origin_ip:
        merlin_path += "ipSrc = {} and ".format(origin_ip)
    if destination_ip:
        merlin_path += "ipDst = {}".format(destination_ip)
    merlin_path = merlin_path.rstrip('and ')

    merlin_targets = ""
    for target_ip in targets_ips:
        merlin_targets += "ipDst = {} and".format(target_ip)
    merlin_targets = merlin_targets.rstrip('and')

    merlin_traffic = ""
    for traffic in traffics:
        merlin_traffic += "{}.dst = {} and".format(traffic[0], traffic[1])
    merlin_traffic = merlin_traffic.rstrip('and')

    merlin_protocols = ""
    for protocol in protocols:
        merlin_protocols += "{} = * and".format(protocol)
    merlin_protocols = merlin_protocols.rstrip('and')

    merlin_services = ""
    for srv in src_services:
        merlin_services += " and ".join(["ipSrc = {}".format(srv_ip) for srv_ip in srv[0]])
        merlin_services += " and tcpSrcPort = {}".format(srv[2])
    for srv in dst_services:
        merlin_services += " and ".join(["ipDst = {}".format(srv_ip) for srv_ip in srv[0]])
        merlin_services += " and tcpDstPort = {}".format(srv[2])

    merlin_predicate = ""
    for merlin_op in [merlin_path, merlin_targets, merlin_traffic, merlin_protocols, merlin_services, merlin_protocols]:
        if merlin_op:
            merlin_predicate += " {} and".format(merlin_op)
    merlin_predicate = merlin_predicate.rstrip('and')

    merlin_rates = ""
    for rate in rates:
        merlin_rates = "{}(x, {}{}) and".format(rate[0], rate[1], rate[2])
    merlin_rates = merlin_rates.rstrip('and')

    merlin_mbs = ""

    middleboxes = filter(None, middleboxes)

    for mb in middleboxes:
        merlin_mbs += "{} .* ".format(mb)

    if merlin_rates:
        merlin_rates = ',\n' + merlin_rates.rstrip(',')

    merlin_intent = """
        [
            x : ({}) -> {}
        ]{}
    """.format(merlin_predicate, merlin_mbs, merlin_rates)
    return merlin_intent


def compile(nile, target="Merlin"):
    """ Compiles Nile intent into target language. By default, the target language is Merlin. """

    start = time.time()
    if target != "Merlin" and target != "Sonata":
        raise ValueError("Target language not yet support. Please contact the repo admin.")

    if target == "Merlin":
        compiled = to_merlin(parse(nile))
    elif target == "Sonata":
        compiled = to_sonata(parse(nile))

    elapsed_time = time.time() - start
    storage.insert(nile, compiled)

    return compiled, elapsed_time


def handle_request(request):
    """ handles requests """
    status = {
        'code': 200,
        'details': 'Deployment success.'
    }

    intent = request.get('intent')
    policy = None
    try:
        policy = compile(intent)
        merlin_deployer.deploy(policy)
    except ValueError as err:
        print 'Error: {}'.format(err)
        status = {
            'code': 404,
            'details': str(err)
        }

    return {
        'status': status,
        'input': {
            'type': 'nile',
            'intent': intent
        },
        'output': {
            'type': 'merlin program',
            'policy': policy
        }
    }


if __name__ == "__main__":
    test_intent = "define intent uniIntent: from endpoint('19.16.1.1') to service('netflix') add middlebox('loadbalancer'), middlebox('firewall') start hour('10:00') end hour('10:00')"
    merlin, compile_time = compile(test_intent)
    deploy_time = merlin_deployer.deploy(merlin)

    print("Deploy time: ", deploy_time)
