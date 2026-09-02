from odoo import http

from odoo.addons.web.controllers.session import Session


class SessionLogout(Session):
    # If it was possible the default redirect would be changed.
    # That does not work when http_routing is installed or any module that would change
    # logout.
    @http.route("/web/session/logout", type="http", auth="none")
    def logout(self, redirect="/web"):  # pylint: disable=unused-argument
        user = (
            http.request.env["res.users"].sudo().browse(http.request.context.get("uid"))
        )
        if user.oauth_provider_id and user.oauth_access_token:
            user._logout_from_keycloak()
            redirect = ""
        return super().logout(redirect=redirect)
