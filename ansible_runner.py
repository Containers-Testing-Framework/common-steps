from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.playbook.play import Play
from ansible.inventory import Inventory
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
import logging


class ResultCallback(CallbackBase):
    result = {}

    def v2_runner_on_ok(self, result, **kwargs):
        self.result = {'contacted': {result._host: result._result}}

    def v2_runner_on_failed(self, result, **kwargs):
        self.result = {'contacted': {result._host: result._result}}

    def v2_runner_on_unreachable(self, result, **kwargs):
        self.result = {'dark': result._host, 'result': result._result}


class Runner(object):
    def __init__(self, inventory_file, module_name, module_args):
        loader = DataLoader()
        variable_manager = VariableManager()

        inventory = Inventory(loader=loader,
                              variable_manager=variable_manager,
                              host_list=inventory_file)
        variable_manager.set_inventory(inventory)

        hosts = [x.name for x in inventory.get_hosts()]

        play_source = {
            "name": "Ansible Play",
            "hosts": hosts,
            "gather_facts": "no",
            "tasks": [{
                "action": {
                    "module": module_name,
                    "args": module_args
                }
            }]
        }
        logging.info(play_source)
        play = Play().load(play_source,
                           variable_manager=variable_manager,
                           loader=loader)

        Options = namedtuple('Options', ['connection', 'module_path', 'forks',
                                         'become', 'become_method',
                                         'become_user', 'check'])
        options = Options(connection='local',
                          module_path='',
                          forks=100,
                          become=None,
                          become_method=None,
                          become_user=None,
                          check=False)

        self.inventory = inventory
        self.variable_manager = variable_manager
        self.loader = loader
        self.play = play
        self.options = options
        self.passwords = {"vault_pass": 'secret'}

    def run(self):
        result = {}
        results_callback = ResultCallback()
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=results_callback
            )
            tqm.run(self.play)
        finally:
            result = results_callback.result
            if tqm is not None:
                tqm.cleanup()
        return result
