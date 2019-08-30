

def validate_no_service_with_capability_exists(service_register, capability, capability_str, auto_configure_property):
    existing_service = service_register.get_service_offering_capability(capability)
    if existing_service is not None:
        raise ValueError('An existing service has been registered to serve the {0} capability but {1} has not been disabled'.format(capability_str, auto_configure_property))
    