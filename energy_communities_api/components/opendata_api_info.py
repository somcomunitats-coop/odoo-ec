from collections import namedtuple

from odoo.addons.component.core import Component


class OpenDataApiInfo(Component):
    _name = "opendata.api.info"
    _inherit = "api.info"
    _usage = "opendata.info"

    QueryResult = namedtuple("QueryResult", ["total"])

    SUMAT_CAMPAIGN_GOAL = 1110

    def get_network_metrics(self):
        return self.work.schema_class(
            members=self.total_members,
            energy_communities_active=self.total_energy_communities_active,
            energy_communities_goal=self.energy_communities_goal,
            energy_communities_total=self.total_energy_communities,
            inscriptions_in_activation=self.total_in_activation_inscriptions,
        )

    @property
    def total_members(self):
        QUERY = """
            select count(*) as total
            from cooperative_membership as cm
            left join res_company as rc on rc.id = cm.company_id
            left join res_partner as rp on rp.id = cm.partner_id
            where
                cm.member is true
                and rp.active
                and rc.hierarchy_level = 'community'
                and rc.name not ilike '%DELETE%'
                and cm.cooperator_register_number is not null
        """
        self.env.cr.execute(QUERY)
        members = self.QueryResult._make(self.env.cr.fetchone())
        return members.total

    @property
    def total_energy_communities_active(self):
        QUERY = """
            select count(*) as total
            from res_company
            where hierarchy_level = 'community' and
            name not ilike '%DELETE%'
        """
        self.env.cr.execute(QUERY)
        comunities = self.QueryResult._make(self.env.cr.fetchone())
        return comunities.total

    @property
    def energy_communities_goal(self):
        return self.SUMAT_CAMPAIGN_GOAL

    @property
    def total_energy_communities(self):
        return (
            self.total_energy_communities_active + self.total_in_activation_inscriptions
        )

    @property
    def total_in_activation_inscriptions(self):
        QUERY = """
            with subm as (
                select
                    place_id,
                    count(id) as submissions
                from crm_lead
                where
                    active
                    and team_id = 5
                group by place_id

            )

            select
                sum(
                    case when subm.submissions > 0 then 1 else 0 end
                ) as xinxetes_sumat_amb_persones
            from cm_place as cmp
            left join subm on subm.place_id = cmp.id
            where
                cmp.presenter_model_id = 4  -- per activar
                and cmp.company_id = 1 -- instancia
                and cmp.status = 'published'
                and cmp.active
        """

        self.env.cr.execute(QUERY)
        inscriptions = self.QueryResult._make(self.env.cr.fetchone())
        if inscriptions.total:
            return inscriptions.total
        return 0
