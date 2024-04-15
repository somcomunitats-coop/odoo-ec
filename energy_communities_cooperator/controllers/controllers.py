# from odoo import http


# class EnergyCommunitiesCooperator(http.Controller):
#     @http.route('/energy_communities_cooperator/energy_communities_cooperator/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/energy_communities_cooperator/energy_communities_cooperator/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('energy_communities_cooperator.listing', {
#             'root': '/energy_communities_cooperator/energy_communities_cooperator',
#             'objects': http.request.env['energy_communities_cooperator.energy_communities_cooperator'].search([]),
#         })

#     @http.route('/energy_communities_cooperator/energy_communities_cooperator/objects/<model("energy_communities_cooperator.energy_communities_cooperator"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('energy_communities_cooperator.object', {
#             'object': obj
#         })
