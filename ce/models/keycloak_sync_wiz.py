# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from argparse import RawDescriptionHelpFormatter
from odoo import fields, models, api, _
from odoo.exceptions import UserError
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

    _KEYCLOAK_UPDATABLE_USER_DATA = [
        'lang', 'groups', 'enabled', 'username', 'email', 'firstname_lastname', 'credentials']

    def _get_client_secret(self, token, id_client):
        clients_endpoint = '{}/{}/client-secret'.format(
            self.endpoint.replace('/users', '/clients'), id_client)

        logger.info(
            'GET KEYCLOAK CLIENT SECRET FOR {}'.format(clients_endpoint))
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }
        resp = requests.get(clients_endpoint, headers=headers, json={})
        self._validate_response(resp, no_json=True)

        return resp.json().get('value', False)

    def _get_clients(self, token, client_id = None):

        clients_endpoint = self.endpoint.replace('/users', '/clients')

        logger.info('GET KEYCLOAK CLIENTS FOR {}'.format(clients_endpoint))
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }
        resp = requests.get(clients_endpoint, headers=headers, json={})
        self._validate_response(resp, no_json=True)

        clients_repr = resp.json()
        if client_id:
            clients_repr = [cli for cli in resp.json() if cli['clientId']==client_id]

        return clients_repr

    # MANAGE REALM DATA ______________________________________________________________

    def _get_realm_groups_data(self, token):
        """Get the JSON Representation of groups of a given REALM.
        It require the KC 'master' admin user have 'query-groups' Client Role assigned for the target realm
        It returns a list of dicts. ex:
        [{
            "id": "8ge163b3-6kc7-40ed-x069-3309eabbcbea",
            "name": "group1",
            "path": "/group1",
            "subGroups": []
        }] """
        target_endpoint = '{}/groups'.format(
            self.endpoint.replace('/users', ''))

        logger.info('GET KEYCLOAK GROUPS DATA FOR REALM %s' % self.endpoint)
        headers = {
            'Authorization': 'Bearer %s' % token,
        }
        resp = requests.get(target_endpoint, headers=headers, json={})
        self._validate_response(resp, no_json=True)

        return resp.json()

    # MANAGE USER DATA ______________________________________________________________

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

    def _get_groups_from_user(self, token, user_keycloak_id):
        """Get the GROUPS JSON Representation of a given keycloak user ID.
        It will retiurn a list of dicts, ex:
        [
            {'id': '72f8045b-984a-4773-bf59-461764c9d16e', 'name': 'ce_admins_group', 'path': '/ce_admins_group'}, 
            {'id': '59139b95-0066-45a6-9b0b-d8bdf4006f87', 'name': 'ce_members_group', 'path': '/ce_members_group'}
        ]
        """
        target_endpoint = '{}/{}/groups'.format(
            self.endpoint, user_keycloak_id)

        logger.info('GET KEYCLOAK USER GROUPS DATA BY ID Calling %s' %
                    self.endpoint)
        headers = {
            'Authorization': 'Bearer %s' % token,
        }
        resp = requests.get(target_endpoint, headers=headers, json={})
        self._validate_response(resp, no_json=True)
        return resp.json()

    def _delete_user_groups_to_user(self, token, user_keycloak_id, group_ids):
        """Remove a given list of KC group_ids from a user."""

        headers = {
            'Authorization': 'Bearer %s' % token,
        }
        try:
            for group_id in group_ids:
                target_endpoint = '{}/{}/groups/{}'.format(
                    self.endpoint, user_keycloak_id, group_id)
                logger.info(
                    'DELETE KEYCLOAK USER GROUP BY ID Calling %s' % self.endpoint)
                requests.delete(target_endpoint, headers=headers, json={})
        except:
            raise UserError(
                _("Error when calling Keycloak API to delete group on user: {}").format(target_endpoint))

        return True

    def _update_user_values(self, odoo_user, kc_data_to_update=[]):
        """Prepare Keycloak UPDATE values for given Odoo user."""

        values = {}

        if not kc_data_to_update:
            # update all the allowed KC user data
            kc_data_to_update = self._KEYCLOAK_UPDATABLE_USER_DATA

        # discart not allowed
        kc_data_to_update = [
            kc_field for kc_field in kc_data_to_update if kc_field in self._KEYCLOAK_UPDATABLE_USER_DATA]

        if 'lang' in kc_data_to_update:
            if values.get('attributes'):
                values['attributes'].update({'lang': odoo_user.lang})
            else:
                values.update({'attributes': {'lang': odoo_user.lang}, })

        if 'groups' in kc_data_to_update:
            ce_roles_map = odoo_user.ce_user_roles_mapping()
            values['groups'] = [
                ce_roles_map[odoo_user.ce_role]['kc_group_name']]

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
                values['firstName'], values['lastName'] = self._split_user_fullname(
                    odoo_user)

        if 'credentials' in kc_data_to_update:
            pass
            # todo: implement here the logic needed to do the password update from Odoo to KC
            #values['credentials'] = [{'type': 'password', 'value': 'w8P=FL_W', 'temporary': False}]

        return values

    def _update_user_by_id(self, token, user_keycloak_id, to_up_data_dict):
        """Update a given keycloak user ID w/ given data."""

        target_endpoint = '{}/{}'.format(self.endpoint, user_keycloak_id)

        logger.info('UPDATE KEYCLOAK USER DATA BY ID Calling %s' %
                    self.endpoint)
        headers = {
            'Authorization': 'Bearer %s' % token,
        }

        try:
            requests.put(target_endpoint, headers=headers,
                         json=to_up_data_dict)
        except:
            raise UserError(
                _("Error when calling Keycloak API to update user: {}").format(target_endpoint))

        return True

    def _add_user_groups_to_user(self, token, user_keycloak_id, group_ids):
        """Assign(add) a given list of KC group_ids to a user."""

        headers = {
            'Authorization': 'Bearer %s' % token,
        }
        try:
            for group_id in group_ids:
                target_endpoint = '{}/{}/groups/{}'.format(
                    self.endpoint, user_keycloak_id, group_id)
                logger.info(
                    'UPDATE KEYCLOAK USER GROUP BY ID Calling %s' % self.endpoint)
                requests.put(target_endpoint, headers=headers, json={})
        except:
            raise UserError(
                _("Error when calling Keycloak API to add group on user: {}").format(target_endpoint))

        return True
