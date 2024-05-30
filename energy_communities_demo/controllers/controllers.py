# from odoo import http


# class EnergyCommunitiesDemo(http.Controller):
#     @http.route('/energy_communities_demo/energy_communities_demo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/energy_communities_demo/energy_communities_demo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('energy_communities_demo.listing', {
#             'root': '/energy_communities_demo/energy_communities_demo',
#             'objects': http.request.env['energy_communities_demo.energy_communities_demo'].search([]),
#         })

#     @http.route('/energy_communities_demo/energy_communities_demo/objects/<model("energy_communities_demo.energy_communities_demo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('energy_communities_demo.object', {
#             'object': obj
#         })
