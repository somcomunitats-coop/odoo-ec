from contextlib import contextmanager

from odoo.api import Environment

from odoo.addons.component.core import Component
from odoo.addons.energy_communities.utils import _get_component

from .config import MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE
from .exceptions import ComponentValidationError


@contextmanager
def subscription_request_utils(env: Environment) -> Component:
    yield _get_component(env, "subscription.request", "subscription.request.utils")


class ValidationMixin:
    def validate(self, _object):
        errors = []
        validate_methods = self.__get_validate_methods()
        for method in validate_methods:
            try:
                method(_object)
            except AssertionError as e:
                errors.append(str(e))
        if errors:
            raise ComponentValidationError(
                MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE["general"],
                errors,
            )
        return True

    def __get_validate_methods(self):
        class_attributes = dir(self)
        is_validate_function = lambda function_name: function_name.startswith(
            "_validate_"
        )

        return [
            getattr(self, function_name)
            for function_name in class_attributes
            if is_validate_function(function_name)
        ]
