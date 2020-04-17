import jinja2 as jinja
from .exceptions import TemplatingError

jinja_env = jinja.Environment(loader=jinja.BaseLoader)

class JinjaTemplate:
    """
    A template is a string with optional placeholders for dynamic data to be injected upon rendering.
    Templates are expected to use the Jinja2 syntax.
    """

    def __init__(self, content):
        """
        Build a template from string

        Args:
            content (str): the string to be rendered
        """
        self.content = content

    def render(self, context):
        """
        Renders the template with Jinja2, passing the context for any data injection

        Args:
            context (dict): the properties that may be referenced in the template
        """
        try:
            rendered_template_content = jinja_env.from_string(self.content).render(context)
            return rendered_template_content
        except jinja.TemplateError as e:
            raise TemplatingError(str(e)) from e

    def __str__(self):
        return f'{self.__class__.__name__}(content: {self.content})'

    def __repr__(self):
        return f'{self.__class__.__name__}(content: {self.content!r}'
