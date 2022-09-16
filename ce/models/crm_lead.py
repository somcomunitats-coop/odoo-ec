from odoo import models, api, fields, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # mapping between the xml_ids related to crm.lead.tag_ids and cm.filter xmlids
    _XMLID_MAPPING_LEADTAGS_CMFILTERS = [
        ('ce_tag_common_generation','ce_cm_filter_community_renewal_generation'),
        ('ce_tag_energy_efficiency','ce_cm_filter_energetic_eficiency'),
        ('ce_tag_sustainable_mobility','ce_cm_filter_sustainable_mobility'),
        ('ce_tag_citizen_education','ce_cm_filter_citizen_education'),
        ('ce_tag_thermal_energy','ce_cm_filter_thermical_energy'),
        ('ce_tag_collective_purchases','ce_cm_filter_collective_purchase'),
        ('ce_tag_renewable_energy','ce_cm_filter_renewal_energy_supply'),
        ('ce_tag_aggregate_demand','ce_cm_filter_demand_flexibility_and_aggregation')
    ]

    lang = fields.Char(string="Language")

    @api.multi
    def _create_map_place_proposal(self):

        active_categ_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_cm_place_category_active')[1]
        building_categ_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_cm_place_category_building')[1]
        default_ce_map_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_default_cm_map')[1]
        creation_ce_source_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_source_creation_ce_proposal')[1]

        for lead in self:

            if not lead.source_id or lead.source_id.id != creation_ce_source_id:
                raise UserError(
                    _("The Source {} of Lead {} do not allow the creation of Map Proposals").format(lead.source_id.name, lead.name))

            place_creation_data = {
                'name': lead.name,
                'map_id': default_ce_map_id,
                'team_type': 'map_place_proposal',
                'user_id': self.env.user.id,
                'proposal_form_submission_id': lead.id,
            }

            # read metadata key/value pairs
            m_dict = {m.key: m.value for m in lead.form_submission_metadata_ids}
            if m_dict.get('legal_state',False) and m_dict['legal_state']:
                if m_dict['legal_state'] == 'active':
                    place_creation_data['place_category_id'] = active_categ_id
                else:
                    place_creation_data['place_category_id'] = building_categ_id
            else:
                raise UserError(
                    _("Unable to get the Category (mandatory map place field) from Lead {}").format(lead.name))

            if m_dict.get('latitude',False) and m_dict['latitude']:
                place_creation_data['lat'] = m_dict['latitude']
            else:
                raise UserError(
                    _("Unable to get the Latitude (mandatory map place field) from Lead {}").format(lead.name))

            if m_dict.get('longitude',False) and m_dict['longitude']:
                place_creation_data['lng'] = m_dict['longitude']
            else:
                raise UserError(
                    _("Unable to get the Longitude (mandatory map place field) from Lead {}").format(lead.name))

            place_creation_data['address_txt'] = lead._get_address_txt() or None
            place_creation_data['filter_mids'] = [(6,0,lead._get_cmfilter_ids())]

            place = self.env['crm.team'].create(place_creation_data)

            # we need to do call those next 2 functions because the @api.onchange('map_id') defined on community_maps module
            # is not being called on crm_team.create(). TODO: review why it happens and fix it.
            place._get_slug_id()
            place._get_config_relations_attrs()

            place.message_subscribe([self.env.user.partner_id.id])

            # lead update
            lead.write({
                'team_id': place.id,
                'submission_type': 'place_proposal_submission',
            })

    @api.multi
    def _get_cmfilter_ids(self):
        self.ensure_one()

        md = self.env['ir.model.data']
        id_pairs = {}
        for pair in self._XMLID_MAPPING_LEADTAGS_CMFILTERS:
            id_pairs[md.get_object_reference('ce', pair[0])[1]] = md.get_object_reference('ce', pair[1])[1]

        return [id_pairs[t.id] for t in self.tag_ids if t.id in id_pairs]

    @api.multi
    def _get_address_txt(self):
        self.ensure_one()

        ret = ''
        meta_address_txt = [meta.value for meta in self.form_submission_metadata_ids if meta.key == 'address_txt']

        if self.street and (self.city or self.zip):
            ret ="{}{}. {}{}".format(
                self.street,
                (self.street2 and ' '+self.street2) or '',
                self.zip or '',
                (self.city and ' '+self.city) or '')
            if self.state_id:
                ret += ', {}'.format(self.state_id.name)
            if self.country_id:
                ret += '. {}'.format(self.country_id.name)
        elif meta_address_txt and meta_address_txt[0]:
            ret = meta_address_txt[0]

        return ret

    @api.multi
    def _build_community_company(self):
        for lead in self:
            pass


class CrmLeadTags(models.Model):
    _inherit = 'crm.lead.tag'

    tag_ext_id = fields.Char('ID Ext tag', compute='compute_ext_id_tag')

    def compute_ext_id_tag(self):
        for record in self:
            res = record.get_external_id()
            record.tag_ext_id = False
            if res.get(record.id):
                record.tag_ext_id = res.get(record.id)