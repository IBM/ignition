import logging
from ignition.service.framework import ServiceRegistration
from ignition.boot.config import BootProperties
from ignition.boot.configurators.utils import validate_no_service_with_capability_exists
from ignition.service.messaging import MessagingProperties, InboxCapability, DeliveryCapability, PostalCapability, PostalService, KafkaDeliveryService, KafkaInboxService

logger = logging.getLogger(__name__)


class MessagingConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        self.__configure_postal(configuration, service_register)
        self.__configure_delivery(configuration, service_register)
        self.__configure_inbox(configuration, service_register)

    def __configure_postal(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.messaging.postal_enabled is True:
            logger.debug('Bootstrapping Messaging Postal Service')
            validate_no_service_with_capability_exists(service_register, PostalCapability, 'Postal Service', 'bootstrap.messaging.postal_enabled')
            service_register.add_service(ServiceRegistration(PostalService, delivery_service=DeliveryCapability))
        else:
            logger.debug('Disabled: bootstrapped Messaging Postal Service')

    def __configure_delivery(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.messaging.delivery_enabled is True:
            logger.debug('Bootstrapping Messaging Delivery Service')
            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            if messaging_config.connection_address is None:
                raise ValueError('messaging.connection_address must be set when bootstrap.messaging.delivery_enabled is True')
            validate_no_service_with_capability_exists(service_register, DeliveryCapability, 'Delivery Service', 'bootstrap.messaging.delivery_enabled')
            service_register.add_service(ServiceRegistration(KafkaDeliveryService, messaging_config=MessagingProperties))
        else:
            logger.debug('Disabled: bootstrapped Messaging Delivery Service')

    def __configure_inbox(self, configuration, service_register):
        auto_config = configuration.property_groups.get_property_group(BootProperties)
        if auto_config.messaging.inbox_enabled is True:
            logger.debug('Bootstrapping Messaging Inbox Service')
            messaging_config = configuration.property_groups.get_property_group(MessagingProperties)
            if messaging_config.connection_address is None:
                raise ValueError('messaging.connection_address must be set when bootstrap.messaging.inbox_enabled is True')
            validate_no_service_with_capability_exists(service_register, InboxCapability, 'Inbox Service', 'bootstrap.messaging.inbox_enabled')
            service_register.add_service(ServiceRegistration(KafkaInboxService, messaging_config=MessagingProperties))
        else:
            logger.debug('Disabled: bootstrapped Messaging Inbox Service')
