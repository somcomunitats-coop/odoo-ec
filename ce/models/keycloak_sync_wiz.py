# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo import fields, models, api, exceptions, _
import logging
import requests
try:
    from json.decoder import JSONDecodeError
except ImportError:
    # py2
    JSONDecodeError = ValueError

logger = logging.getLogger(__name__)

class KeycloakSyncMixin(models.AbstractModel):
    """Synchronize Keycloak users mixin."""

    _inherit = 'auth.keycloak.sync.mixin'

    _KEYCLOAK_UPDATABLE_USER_DATA = ['lang', 'groups', 'enabled', 'username', 'email', 'firstname_lastname', 'credentials']

    def _get_user_by_id(self, token, user_keycloak_id):
        """Get the JSON Representation of a given keycloak user ID"""

        target_endpoint = '{}/{}'.format(self.endpoint, user_keycloak_id)
        
        logger.info('GET KEYCLOAK USER DATA BY ID Calling %s' % self.endpoint)
        headers = {
            'Authorization': 'Bearer %s' % token,
        }
        resp = requests.get(target_endpoint, headers=headers, json={})
        self._validate_response(resp, no_json=True)

        return resp.json()

    def _update_user_values(self, odoo_user, kc_data_to_update=[]):
        """Prepare Keycloak UPDATE values for given Odoo user."""

        values = {}

        if not kc_data_to_update:
            # update all the allowed KC user data
            kc_data_to_update = self._KEYCLOAK_UPDATABLE_USER_DATA

        #discart not allowed
        kc_data_to_update = [kc_field for kc_field in kc_data_to_update if kc_field in self._KEYCLOAK_UPDATABLE_USER_DATA]
        
        if 'lang' in kc_data_to_update:
            if values.get('attributes'):
                values['attributes'].update({'lang': odoo_user.lang})
            else:
                values.update({'attributes':{'lang': odoo_user.lang},})

        if 'groups' in kc_data_to_update:
            UserSudo = self.env['res.users'].sudo()
            ce_roles_map = UserSudo.ce_user_roles_mapping()
            groups_to_update = []
            for k,v in ce_roles_map.items():
                if v in odoo_user.role_ids.ids:
                    groups_to_update.append(k)
            values['groups'] = groups_to_update

        if 'enabled' in kc_data_to_update:
            values['enabled'] = odoo_user.active

        if 'username' in kc_data_to_update:
            values['username'] = odoo_user.login

        if 'email' in kc_data_to_update:
            values['email'] = odoo_user.email

        if 'firstname_lastname' in kc_data_to_update:
            if 'firstname' in odoo_user.partner_id:
                # partner_firstname installed
                values['firstName'] = odoo_user.partner_id.firstname
                values['lastName'] = odoo_user.partner_id.lastname
            else:
                values['firstName'], values['lastName'] = self._split_user_fullname(odoo_user)

        if 'credentials' in kc_data_to_update:
            pass
            # todo: implement here the logic needed to do the password update from Odoo to KC
            #values['credentials'] = [{'type': 'password', 'value': 'w8P=FL_W', 'temporary': False}]

        return values
    
    def _update_user_by_id(self, token, user_keycloak_id, to_up_data_dict):
        """Update a given keycloak user ID w/ given data."""

        target_endpoint = '{}/{}'.format(self.endpoint, user_keycloak_id)

        logger.info('UPDATE KEYCLOAK USER DATA BY ID Calling %s' % self.endpoint)
        headers = {
            'Authorization': 'Bearer %s' % token,
        }
        resp = requests.put(target_endpoint, headers=headers, json=to_up_data_dict)
        self._validate_response(resp, no_json=True)
        
        # only in case we are returning the full KC Data JSON Representantion of the user 
        return self._get_user_by_id(token, user_keycloak_id)
