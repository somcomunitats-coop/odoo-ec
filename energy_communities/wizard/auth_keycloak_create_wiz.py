from odoo import fields, models, api


class KeycloakCreateWiz(models.TransientModel):
    """Export Odoo users to Keycloak.

    Usually Keycloak is already populated w/ your users base.
    Many times this will come via LDAP, AD, pick yours.

    Still, you might need to push some users to Keycloak on demand,
    maybe just for testing.

    If you need this, this is the wizard for you ;)
    """

    _inherit = 'auth.keycloak.create.wiz'

    def _create_user_values(self, odoo_user):
        """Prepare Keycloak values for given Odoo user."""

        values = super(KeycloakCreateWiz,self)._create_user_values(odoo_user)

        if self._context.get('kc_user_creation_vals'):
            values.update(self._context.get('kc_user_creation_vals'))

        return values
