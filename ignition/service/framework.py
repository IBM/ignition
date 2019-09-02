from abc import ABC, abstractmethod
import networkx as nx

interface = abstractmethod


class Capability(ABC):

    def __init__(self):
        super().__init__()


class Service(ABC):

    def __init__(self):
        super().__init__()


class ServiceRegistration():

    def __init__(self, service_class, *args, **required_capabilities):
        self.service_class = service_class
        self.provided = False
        self.args = args
        self.required_capabilities = required_capabilities


class ServiceRegister():

    SERVICE_TYPE = 'Service'
    CAPABILITY_TYPE = 'Capability'

    OFFERS_CAPABILITY_LABEL = 'offersCapability'
    REQUIRES_CAPABILITY_LABEL = 'requiresCapability'

    def __init__(self):
        self.service_graph = nx.DiGraph()

    def add_service(self, service_registration):
        service_class = service_registration.service_class
        if not issubclass(service_class, Service):
            raise NotAServiceException('Service class argument given is not a subclass of Service: {0}'.format(service_class), service_class)
        self.__check_for_duplicate_service_node(service_class)
        self.__check_for_duplicate_capabilities(service_class)
        self.__add_service_node(service_class, service_registration.args, service_registration.provided)
        self.__register_service_capabilities(service_class)
        self.__register_service_requirements(service_class, service_registration.required_capabilities)

    def get_services(self):
        return self.__get_service_classes()

    def get_capabilities(self):
        return self.__get_capability_classes()

    def get_service_offering_capability(self, capability_class):
        return self.__get_service_offering_capability(capability_class)

    def get_service_required_capabilities(self, service_class):
        return self.__get_service_required_capabilities(service_class)

    def get_service_requirements(self, service_class):
        return self.__get_service_requirements(service_class)

    def get_service_args(self, service_class):
        service_node = self.__get_opt_node(self.SERVICE_TYPE, service_class)
        if service_node is None:
            raise ServiceNotFoundException('Service \'{0}\' not found'.format(service_class), service_class)
        return service_node['args']

    def is_service_set_as_provided(self, service_class):
        service_node = self.__get_opt_node(self.SERVICE_TYPE, service_class)
        if service_node is None:
            raise ServiceNotFoundException('Service \'{0}\' not found'.format(service_class), service_class)
        return service_node['provided']

    def order_services_by_requirements(self):
        req_graph = self.__build_requirements_graph(enforce_capability_offered=True)
        self.__check_for_cycles_in_req_graph(req_graph)
        # Order
        ordered_service_keys = list(nx.dfs_postorder_nodes(req_graph))
        ordered_service_classes = []
        for service_key in ordered_service_keys:
            ordered_service_classes.append(req_graph.nodes[service_key]['data'])
        return ordered_service_classes

    def __node_key(self, node_type, node_id):
        return '{0}-{1}'.format(node_type, hash(node_id))

    def __get_opt_node(self, node_type, node_id):
        node_key = self.__node_key(node_type, node_id)
        if node_key not in self.service_graph.nodes:
            return None
        return self.service_graph.nodes[node_key]

    def __get_opt_service_node(self, service_class):
        return self.__get_opt_node(self.SERVICE_TYPE, service_class)

    def __get_opt_capability_node(self, capability_class):
        return self.__get_opt_node(self.CAPABILITY_TYPE, capability_class)

    def __service_key(self, service_class):
        return self.__node_key(self.SERVICE_TYPE, service_class)

    def __capability_key(self, capability_class):
        return self.__node_key(self.CAPABILITY_TYPE, capability_class)

    def __check_for_duplicate_service_node(self, service_class):
        existing_service_node = self.__get_opt_service_node(service_class)
        if existing_service_node is not None:
            raise DuplicateServiceException('Attempting to add a duplicate service: {0}'.format(service_class), service_class)

    def __read_capabilities_from_service_class(self, service_class):
        capability_classes = []
        parent_classes = service_class.__mro__
        for parent_class in parent_classes:
            if issubclass(parent_class, Capability) and parent_class is not Capability:
                capability_classes.append(parent_class)
        return capability_classes

    def __check_for_duplicate_capabilities(self, service_class):
        capability_classes = self.__read_capabilities_from_service_class(service_class)
        for capability_class in capability_classes:
            existing_capability = self.__get_opt_capability_node(capability_class)
            if existing_capability is not None:
                service_offering_capability = self.__get_service_offering_capability(capability_class)
                if service_offering_capability is not None:
                    raise DuplicateCapabilityException('Service \'{0}\' offers capability \'{1}\' which has already been offered by \'{2}\''.format(
                        service_class, capability_class, service_offering_capability), service_class, capability_class, service_offering_capability)

    def __add_service_node(self, service_class, args, provided=False):
        self.service_graph.add_node(self.__service_key(service_class), data=service_class, node_type=self.SERVICE_TYPE, args=args, provided=provided)

    def __add_capability_node(self, capability_class):
        self.service_graph.add_node(self.__capability_key(capability_class), data=capability_class, node_type=self.CAPABILITY_TYPE)

    def __link_service_offering_capability(self, service_class, capability_class):
        self.service_graph.add_edge(self.__service_key(service_class), self.__capability_key(capability_class), label=self.OFFERS_CAPABILITY_LABEL)

    def __link_service_requiring_capability(self, service_class, capability_class, requirement_name):
        self.service_graph.add_edge(self.__service_key(service_class), self.__capability_key(capability_class), label=self.REQUIRES_CAPABILITY_LABEL, requirement_name=requirement_name)

    def __get_service_offering_capability(self, capability_class):
        edge_query = EdgeQuery(self.__capability_key(capability_class))
        edge_query.edge_label = self.OFFERS_CAPABILITY_LABEL
        edge_query.expecting_single = True
        edge_query.other_type = self.SERVICE_TYPE
        edge_query.outgoing = False
        related_node_key = EdgeQueryHandler(self.service_graph, edge_query).execute()
        if related_node_key is None:
            return None
        service_node = self.service_graph.nodes[related_node_key]
        return service_node['data']

    def __get_service_required_capabilities(self, service_class):
        service_node = self.__get_opt_service_node(service_class)
        if service_node is None:
            raise ServiceNotFoundException('Service \'{0}\' not found'.format(service_class), service_class)
        edge_query = EdgeQuery(self.__service_key(service_class))
        edge_query.edge_label = self.REQUIRES_CAPABILITY_LABEL
        edge_query.expecting_single = False
        edge_query.other_type = self.CAPABILITY_TYPE
        edge_query.outgoing = True
        related_node_keys = EdgeQueryHandler(self.service_graph, edge_query).execute()
        result = []
        for related_node_key in related_node_keys:
            node = self.service_graph.nodes[related_node_key]
            result.append(node['data'])
        return result

    def __get_service_requirements(self, service_class):
        service_node = self.__get_opt_service_node(service_class)
        if service_node is None:
            raise ServiceNotFoundException('Service \'{0}\' not found'.format(service_class), service_class)
        edge_query = EdgeQuery(self.__service_key(service_class))
        edge_query.edge_label = self.REQUIRES_CAPABILITY_LABEL
        edge_query.expecting_single = False
        edge_query.other_type = self.CAPABILITY_TYPE
        edge_query.outgoing = True
        edge_query.return_with_edges = True
        results = EdgeQueryHandler(self.service_graph, edge_query).execute()
        requirements = {}
        for result in results:
            edge = result['edge']
            node = self.service_graph.nodes[result['related_node_key']]
            requirements[edge['requirement_name']] = node['data']
        return requirements

    def __register_service_capabilities(self, service_class):
        capability_classes = self.__read_capabilities_from_service_class(service_class)
        for capability_class in capability_classes:
            self.__add_capability_node(capability_class)
            self.__link_service_offering_capability(service_class, capability_class)

    def __register_service_requirements(self, service_class, required_capabilities):
        for requirement_name, required_capability_class in required_capabilities.items():
            if not issubclass(required_capability_class, Capability):
                raise RequirementNotACapabilityException('Service \'{0}\' not allowed requirement to class \'{1}\' as it does not subclass Capability'.format(
                    service_class, required_capability_class), service_class, required_capability_class)
            if self.__get_opt_capability_node(required_capability_class) is None:
                self.__add_capability_node(required_capability_class)
            self.__link_service_requiring_capability(service_class, required_capability_class, requirement_name)

    def __get_service_classes(self):
        service_classes = []
        for node_key in self.service_graph.nodes:
            node = self.service_graph.nodes[node_key]
            if node['node_type'] is self.SERVICE_TYPE:
                service_classes.append(node['data'])
        return service_classes

    def __get_capability_classes(self):
        capability_classes = []
        for node_key in self.service_graph.nodes:
            node = self.service_graph.nodes[node_key]
            if node['node_type'] is self.CAPABILITY_TYPE:
                capability_classes.append(node['data'])
        return capability_classes

    def __build_requirements_graph(self, enforce_capability_offered=False):
        req_graph = nx.DiGraph()
        # Add all Services to a new graph
        service_classes = self.__get_service_classes()
        for service_class in service_classes:
            req_graph.add_node(self.__service_key(service_class), data=service_class)

        # For each Service, add an edge in the new graph, to the Service offering the capability the first Component requires
        for service_class in service_classes:
            required_capabilities = self.__get_service_required_capabilities(service_class)
            for capability_class in required_capabilities:
                service_class_offering_capability = self.__get_service_offering_capability(capability_class)
                if service_class_offering_capability is not None:
                    req_graph.add_edge(self.__service_key(service_class), self.__service_key(service_class_offering_capability))
                elif enforce_capability_offered:
                    raise RequiredCapabilityNotOffered('No service found offering capability \'{0}\' required by service \'{1}\''.format(
                        capability_class, service_class), capability_class, service_class)

        return req_graph

    def __check_for_cycles_in_req_graph(self, req_graph):
        cycles = list(nx.simple_cycles(req_graph))
        if len(cycles) > 0:
            cyclic_dependencies_for_exception = []
            cycle_report = ''
            for chain in cycles:
                chain_service_classes = []
                for key in chain:
                    service_node = self.service_graph.nodes[key]
                    chain_service_classes.append(service_node['data'])
                # Add first to the end, to better display cyclic link
                chain_service_classes.append(chain_service_classes[0])
                if len(cycle_report) > 0:
                    cycle_report += '\n'
                cycle_report += str(chain_service_classes)
                first_and_second_dependent_keys = [chain[0], chain[len(chain)-1]]
                first_and_second_dependent_keys.sort()
                first_dependent = self.service_graph.nodes[first_and_second_dependent_keys[0]]['data']
                second_dependent = self.service_graph.nodes[first_and_second_dependent_keys[1]]['data']
                cyclic_dependencies_for_exception.append(CyclicDependency(first_dependent, second_dependent, chain_service_classes))
            raise CyclicDependencyException('The following services have a cyclic dependency: \n{0}'.format(cycle_report), cyclic_dependencies_for_exception)


class EdgeQuery():

    def __init__(self, starting_key):
        self.starting_key = starting_key
        self.other_type = None
        self.edge_label = None
        self.outgoing = True
        self.expecting_single = False
        self.return_with_edges = False


class EdgeQueryHandler():

    def __init__(self, graph, query):
        self.graph = graph
        self.query = query

    def execute(self):
        key = self.query.starting_key
        if key not in self.graph.nodes:
            results = []
        else:
            if self.query.outgoing is True:
                results = list(self.graph.successors(key))
            else:
                results = list(self.graph.predecessors(key))
            if self.query.edge_label is not None:
                results = self.__reduce_by_edge_label(key, results)
            if self.query.other_type is not None:
                results = self.__reduce_by_other_type(key, results)
            if self.query.return_with_edges is True:
                results = self.__include_edges(key, results)
        if self.query.expecting_single is True:
            return self.__return_single_result(results)
        else:
            return results

    def __reduce_by_edge_label(self, starting_key, related_node_keys):
        matching = []
        for related_node_key in related_node_keys:
            if self.query.outgoing is True:
                edge = self.graph[starting_key][related_node_key]
            else:
                edge = self.graph[related_node_key][starting_key]
            if edge['label'] is self.query.edge_label:
                matching.append(related_node_key)
        return matching

    def __reduce_by_other_type(self, starting_key, related_node_keys):
        matching = []
        for related_node_key in related_node_keys:
            if self.query.outgoing is True:
                edge = self.graph[starting_key][related_node_key]
            else:
                edge = self.graph[related_node_key][starting_key]
            related_node = self.graph.nodes[related_node_key]
            if related_node['node_type'] is self.query.other_type:
                matching.append(related_node_key)
        return matching

    def __include_edges(self, starting_key, related_node_keys):
        results = []
        for related_node_key in related_node_keys:
            if self.query.outgoing is True:
                edge = self.graph[starting_key][related_node_key]
            else:
                edge = self.graph[related_node_key][starting_key]
            related_node = self.graph.nodes[related_node_key]
            results.append({'related_node_key': related_node_key, 'edge': edge})
        return results

    def __return_single_result(self, results):
        if len(results) > 1:
            raise StoreException(self.single_result_failure(len(results)))
        elif len(results) > 0:
            return results[0]
        else:
            return None

    def single_result_failure(self, found_number):
        if self.query.outgoing is True:
            direction = 'outgoing'
        else:
            direction = 'incoming'
        return 'Expected only a single entity related to entity \'{0}\' with {1} edge labelled \'{2}\' but found {3}'.format(self.query.starting_key, direction, self.query.edge_label, found_number)


class ServiceInstances():

    def __init__(self):
        self.instances_by_service_class = {}

    def add_instance_of(self, instance, service_class):
        key = service_class
        if key in self.instances_by_service_class:
            raise ValueError('Instances already exists for service_class: {0}'.format(service_class))
        self.instances_by_service_class[service_class] = instance

    def get_instance(self, service_class):
        if service_class not in self.instances_by_service_class:
            return None
        return self.instances_by_service_class[service_class]


class ServiceInitialiser():

    def __init__(self, service_instances, service_register):
        self.service_instances = service_instances
        self.service_register = service_register

    def build_instances(self):
        ordered_service_classes = self.service_register.order_services_by_requirements()
        for service_class in ordered_service_classes:
            is_provided = self.service_register.is_service_set_as_provided(service_class)
            if not is_provided:
                self.__build_instance_of_service(service_class)

    def __build_instance_of_service(self, service_class):
        required_capabilities = self.service_register.get_service_requirements(service_class)
        capability_instances_args = {}
        for requirement_name, required_capability in required_capabilities.items():
            required_service = self.service_register.get_service_offering_capability(required_capability)
            if required_service is None:
                raise RequiredCapabilityNotOffered('No service found offering capability \'{0}\' required by service \'{1}\''.format(
                    required_capability, service_class), required_capability, service_class)
            instance_of_required_service = self.service_instances.get_instance(required_service)
            if instance_of_required_service is None:
                raise NoServiceInstanceException('No instance of service \'{0}\' has been created, required by \'{1}\''.format(required_service, service_class), required_service, service_class)
            capability_instances_args[requirement_name] = instance_of_required_service
        service_args = self.service_register.get_service_args(service_class)
        service_instance = service_class(*service_args, **capability_instances_args)
        self.service_instances.add_instance_of(service_instance, service_class)


class NoServiceInstanceException(Exception):

    def __init__(self, message, service_class, required_by_service_class):
        super().__init__(message)
        self.service_class = service_class
        self.required_by_service_class = required_by_service_class


class NotAServiceException(Exception):

    def __init__(self, message, problem_class):
        super().__init__(message)
        self.problem_class = problem_class


class DuplicateCapabilityException(Exception):

    def __init__(self, message, offending_service_class, capability_class, original_service_class):
        super().__init__(message)
        self.offending_service_class = offending_service_class
        self.original_service_class = original_service_class
        self.capability_class = capability_class


class DuplicateServiceException(Exception):

    def __init__(self, message, service_class):
        super().__init__(message)
        self.service_class = service_class


class ServiceNotFoundException(Exception):

    def __init__(self, message, service_class):
        super().__init__(message)
        self.service_class = service_class


class RequirementNotACapabilityException(Exception):

    def __init__(self, message, service_class, offending_capability_class):
        super().__init__(message)
        self.service_class = service_class
        self.offending_capability_class = offending_capability_class


class CyclicDependencyException(Exception):

    def __init__(self, message, cyclic_dependencies):
        super().__init__(message)
        self.cyclic_dependencies = cyclic_dependencies


class CyclicDependency():

    def __init__(self, first_dependent, second_dependent, chain):
        self.first_dependent = first_dependent
        self.second_dependent = second_dependent
        self.chain = chain


class RequiredCapabilityNotOffered(Exception):

    def __init__(self, message, capability_class, required_by_service_class):
        super().__init__(message)
        self.capability_class = capability_class
        self.required_by_service_class = required_by_service_class
