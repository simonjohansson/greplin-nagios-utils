import os
import sys
import re
import pkgutil
import greplin_nagios_utils.AngryCron.Scripts


class DynamicLoadRunner(object):
    """Automatically discover services."""

    def __init__(self, module):
        self.services = {}
        self.load_services(module)

    def get_services(self):
        return self.services

    def load_services(self, module):
        package = sys.modules[module]
        for imprt, mod_name, ispkg in pkgutil.iter_modules(package.__path__):
            full_submodule_name = ".".join([module, mod_name])
            __import__(full_submodule_name)
            submodule = sys.modules[full_submodule_name]
            if hasattr(submodule, 'service'):
                print 'loading %s from %s' % (mod_name, full_submodule_name)
                service_function = getattr(submodule, 'check')
                self.services[mod_name] = service_function
