from odoo import api, models, fields, _
import logging

logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _generate_signup_values(self, provider, validation, params):
        """
        Overwrite method to get user values with user_id not email
        :param provider:
        :param validation:
        :param params:
        :return:
        """
        values = super(ResUsers, self)._generate_signup_values(provider, validation, params)
        values['login'] = validation['user_id']
        return values

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        users.create_users_on_keycloak()
        return users

    def create_users_on_keycloak(self):
        """Create users on Keycloak.

        1. get a token
        2. loop on given users
        3. push them to Keycloak if:
           a. missing on Keycloak
           b. they do not have an Oauth UID already
        4. brings you to update users list
        """
        logger.debug('Create keycloak user START')
        token = self.env.user.oauth_access_token
        logger.info(
            'Creating users for %s' % ','.join(self.user_ids.mapped('login'))
        )
        for user in self.user_ids:
            if user.oauth_uid:
                # already sync'ed somewhere else
                continue
            # keycloak_user = self._get_or_create_user(token, user)
            '''user.update({
                'oauth_uid': keycloak_user['id'],
                'oauth_provider_id': self.provider_id.id,
            })'''
        # action = self.env.ref('base.action_res_users').read()[0]
        # action['domain'] = [('id', 'in', self.user_ids.ids)]
        logger.debug('Create keycloak users STOP')
        return True
