import connexion

OPERATION_ID_PREFIX = '.'

def build_resolver_func_to_instance(instance):
    def resolve_operation(function_name):
        if function_name is None:
            raise ValueError("Empty function name")
        prefix = OPERATION_ID_PREFIX
        if function_name.startswith(prefix):
            the_rest = function_name[function_name.index(prefix) + len(prefix):]
            current_obj = instance
            parts = the_rest.split('.')
            current_part_num = 0
            while current_part_num < len(parts):
                next_part = parts[current_part_num]
                if hasattr(current_obj, next_part):
                    current_obj = getattr(current_obj, next_part)
                else:
                    raise ValueError('Cound not find {0} in {1}'.format(next_part, current_obj))
                current_part_num+=1
            return current_obj
        else:
            return connexion.utils.get_function_from_name(function_name)
    return resolve_operation

def build_resolver_to_instance(instance):
    resolver = connexion.resolver.Resolver()
    resolver.function_resolver = build_resolver_func_to_instance(instance)
    return resolver

# Custom validator that allows the validator errors to be caught later in the stack. 
# The out-of-the-box impl by connexion catches the errors and configures the Rest response, we want our own response format to be determined by the error_converter on the application configuration
class RequestBodyValidator(connexion.decorators.validation.RequestBodyValidator):
    def validate_schema(self, data, url):
        if self.is_null_value_valid and connexion.utils.is_null(data):
            return None
        self.validator.validate(data)