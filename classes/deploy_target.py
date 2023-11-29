from abc import ABC, abstractmethod
import re

from deployer import merlin as merlin_deployer
from .controller_methods import ControllerMethods

class DeployTarget(ControllerMethods, ABC):
 
    def __init__(self):
        self.controllerIps = []

   
    def parseNile(self):
        """ Parses a Nile intent from text and return dictionary with intent operation targets """
        from_pattern = re.compile(r".*from (endpoint|service)(\(\'.*?\'\)).*")
        to_pattern = re.compile(r".*to (endpoint|service)(\(\'.*?\'\)).*")
        target_pattern = re.compile(r".*for ((endpoint|service|group|traffic)(\(\'.*?\'\))(, (endpoint|service|group|traffic)(\(\'.*?\'\)))*).*")
        set_unset_pattern = re.compile(r".*(set|unset) ((quota|bandwidth)(\(\'.*?\'\))(, (quota|bandwidth)(\(\'.*?\'\)))*).*")
        allow_block_pattern = re.compile(r".*(allow|block) ((traffic|service|protocol)(\(\'.*?\'\))(, (traffic|service|protocol)(\(\'.*?\'\)))*).*")
        add_remove_pattern = re.compile(r".*(add|remove) ((middlebox)(\(\'.*?\'\))(, (middlebox)(\(\'.*?\'\)))*).*")
        start_pattern = re.compile(r".*start (hour|datetime|timestamp)(\(\'.*?\'\)).*")
        end_pattern = re.compile(r".*end (hour|datetime|timestamp)(\(\'.*?\'\)).*")

        op_targets = {
            'operations': [],
            'targets': []
        }

        result = from_pattern.search(self)
        if result:
            op_targets['origin'] = {
                'function': result.group(1),
                'value': result.group(2)
            }

        result = to_pattern.search(self)
        if result:
            op_targets['destination'] = {
                'function': result.group(1),
                'value': result.group(2)
            }

        results = re.findall(target_pattern, self)
        if results:
            result = results[0]
            for idx, match in enumerate(result):
                if idx != 0:
                    val = result[idx + 1] if idx + 1 < len(result) else ""
                    val = val.rstrip(',')
                    op_targets['targets'].append({
                        'function': match,
                        'value': val
                    })

        results = re.findall(set_unset_pattern, self)
        if results:
            result = results[0]
            operation = ''
            for idx, match in enumerate(result):
                if idx == 0:
                    operation = match
                else:
                    if idx != 1 and idx % 2 == 0 and match:
                        val = result[idx + 1] if idx + 1 < len(result) else ""
                        val = val.rstrip(',')
                        op_targets['operations'].append({
                            'type': operation,
                            'function': match,
                            'value': val
                        })

        results = re.findall(allow_block_pattern, self)
        if results:
            result = results[0]
            operation = ''
            for idx, match in enumerate(result):
                if idx == 0:
                    operation = match
                else:
                    if idx != 1 and idx % 2 == 0 and match:
                        val = result[idx + 1] if idx + 1 < len(result) else ""
                        val = val.rstrip(',')
                        op_targets['operations'].append({
                            'type': operation,
                            'function': match,
                            'value': val
                        })

        results = re.findall(add_remove_pattern, self)
        if results:
            result = results[0]
            operation = ''
            for idx, match in enumerate(result):
                if idx == 0:
                    operation = match
                elif 'middlebox' not in match:
                    op_targets['operations'].append({
                        'type': operation,
                        'value': match
                    })

        result = start_pattern.search(self)
        if result:
            op_targets['start'] = {
                'function': result.group(1),
                'value': result.group(2)
            }

        result = end_pattern.search(self)
        if result:
            op_targets['end'] = {
                'function': result.group(1),
                'value': result.group(2)
            }

        return op_targets
    
    @abstractmethod
    def handleRequest(self, request):
        pass
    
    @abstractmethod
    def compile(self):
        pass
