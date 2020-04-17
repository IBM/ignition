from .exceptions import InvalidDeploymentLocationError

def get_property_or_default(properties, *keys, default_provider=None, error_if_not_found=False):
    """
    Searches a properties dictionary for a value of the first matching key. If none of the keys are found then a default may be returned or an error thrown

    Args:
        properties (dict): dictionary of properties to search in 
        *keys (str): the keys to search for in the properties
        default_provider (obj or callable): a default value or callable function which returns a default value. Defaults to None
        error_if_not_found (bool): enable to raise an error instead of returning a default value if none of the keys are found. Defaults to False

    Raises:
        InvalidDeploymentLocationError: if error_if_not_found argument is True and none of the keys were found
    """
    if len(keys) == 0:
        raise ValueError('Must provide at least one key to find property')
    value = None
    value_found = False
    for key in keys:
        if key in properties:
            value_found = True
            value = properties.get(key)
            break
    # Can't base this on value being not None as it may have been set to None deliberately
    if not value_found:
        if error_if_not_found:
            error_msg = f'Deployment location properties missing value for property \'{keys[0]}\''
            if len(keys) > 1:
                error_msg += ' (or: '
                for idx, k in enumerate(keys):
                    if idx != 0:
                        if idx != 1:
                            error_msg += ', '
                        error_msg += f'\'{k}\''
                error_msg += ')'
            raise InvalidDeploymentLocationError(error_msg)
        if callable(default_provider):
            return default_provider()
        else:
            return default_provider
    else:
        return value