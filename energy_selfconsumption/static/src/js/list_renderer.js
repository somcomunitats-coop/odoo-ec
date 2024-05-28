odoo.define('energy_selfconsumption.ListRenderer', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var ListView = require('web.ListView');
    var view_registry = require('web.view_registry');
    var rpc = require('web.rpc');

    var ListRendererDistributionTable = ListRenderer.extend({
        _onRowClicked: function (event) {
            if ($(event.target)[0].className !== 'custom-control-label'
                && $(event.target)[0].className !== 'custom-control-input')  {
                var self = this;
                var id = $(event.currentTarget).data('id');
                var found = this.state.data.find((element) => element.id == id);

                rpc.query({
                    model: 'energy_selfconsumption.distribution_table',
                    method: 'action_open_form',
                    args: [[found.res_id]],
                }).then(function (action){
                    self.do_action(action);
                });
            }
        },
    });

    var DistributionTableView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Renderer: ListRendererDistributionTable,
        }),
    });

    view_registry.add('distribution_table', DistributionTableView);
});
