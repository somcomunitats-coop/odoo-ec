# from odoo import http


# class MassMailingMulticompany(http.Controller):
#     @http.route('/mass_mailing_multicompany/mass_mailing_multicompany/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mass_mailing_multicompany/mass_mailing_multicompany/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mass_mailing_multicompany.listing', {
#             'root': '/mass_mailing_multicompany/mass_mailing_multicompany',
#             'objects': http.request.env['mass_mailing_multicompany.mass_mailing_multicompany'].search([]),
#         })

#     @http.route('/mass_mailing_multicompany/mass_mailing_multicompany/objects/<model("mass_mailing_multicompany.mass_mailing_multicompany"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mass_mailing_multicompany.object', {
#             'object': obj
#         })
