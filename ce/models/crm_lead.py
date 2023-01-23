from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime


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
    ce_tag_ids = fields.Many2many('crm.lead.tag', 'crm_lead_ce_tag_rel', 'lead_id', 'tag_id', string='CE Tags', help="CE Classify and analyze categories")

    community_company_id = fields.Many2one(
        string='Related Community',
        comodel_name='res.company',
        domain="[('coordinator','!=',True)]",
        help="Community related to this Lead"
    )

    @api.multi
    def _create_map_place_proposal(self):

        if not self.env.user.company_id.coordinator:
            raise UserError(
                _("Only users that belongs to the 'Coordinator' company can create new Map Places from Leads."))

        active_categ_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_cm_place_category_active')[1]
        building_categ_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_cm_place_category_building')[1]
        default_ce_map_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_default_cm_map')[1]
        creation_ce_source_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_source_creation_ce_proposal')[1]

        for lead in self:

            if self.env['crm.team'].search([('proposal_form_submission_id','=',lead.id), ('map_id','=',default_ce_map_id)]):
                raise UserError(
                    _("There is an allready existing Map Place related to this Lead: {}.").format(lead.name))

            if not lead.source_id or lead.source_id.id != creation_ce_source_id:
                raise UserError(
                    _("The Source {} of Lead {} do not allow the creation of Map Proposals").format(lead.source_id.name, lead.name))

            place_creation_data = {
                'name': lead.name,
                'map_id': default_ce_map_id,
                'team_type': 'map_place_proposal',
                'user_id': self.env.user.id,
                'proposal_form_submission_id': lead.id,
                'interaction_method': 'external_link',
                'external_link_target': '_top',
            }

            # read metadata key/value pairs
            m_dict = {m.key: m.value for m in lead.form_submission_metadata_ids}

            if m_dict.get('partner_legal_state',False) and m_dict['partner_legal_state']:
                if m_dict['partner_legal_state'] == 'active':
                    place_creation_data['place_category_id'] = active_categ_id
                else:
                    place_creation_data['place_category_id'] = building_categ_id
            else:
                raise UserError(
                    _("Unable to get the Category (mandatory map place field) from Lead: {}").format(lead.name))

            if m_dict.get('partner_latitude',False) and m_dict['partner_latitude']:
                place_creation_data['lat'] = m_dict['partner_latitude']
            else:
                raise UserError(
                    _("Unable to get the Latitude (mandatory map place field) from Lead: {}").format(lead.name))

            if m_dict.get('partner_longitude',False) and m_dict['partner_longitude']:
                place_creation_data['lng'] = m_dict['partner_longitude']
            else:
                raise UserError(
                    _("Unable to get the Longitude (mandatory map place field) from Lead: {}").format(lead.name))

            if m_dict.get('partner_map_place_form_url',False) and m_dict['partner_map_place_form_url']:
                place_creation_data['external_link_url'] = m_dict['partner_map_place_form_url']

            place_creation_data['address_txt'] = lead._get_address_txt() or None
            place_creation_data['filter_mids'] = [(6,0,lead._get_cmfilter_ids())]

            place = self.env['crm.team'].create(place_creation_data)

            # we need to do call those next 2 functions because the @api.onchange('map_id') defined on community_maps module
            # is not being called on crm_team.create(). TODO: review why it happens and fix it.
            place._get_slug_id()
            place._get_config_relations_attrs()
            place._build_presenter_metadata_ids()
            place.place_category_id = place_creation_data['place_category_id']

            place.message_subscribe([self.env.user.partner_id.id])

            pmnd_ids = [m for m in place.place_presenter_metadata_ids if m.key == 'p_description']
            description_pmnd_id = pmnd_ids and pmnd_ids[0] or None
            if description_pmnd_id and lead.description:
                description_pmnd_id.value = "<p class='m-2'>{}</p>".format(lead.description)

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
        meta_address_txt = [meta.value for meta in self.form_submission_metadata_ids if meta.key == 'partner_full_address']

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

        if not self.env.user.company_id.coordinator:
            raise UserError(
                _("Only users that belongs to the 'Coordinator' company can create new Companies from Leads."))

        creation_ce_source_id = self.env['ir.model.data'].get_object_reference('ce', 'ce_source_creation_ce_proposal')[1]

        # build company for each Lead
        for lead in self:

            if not lead.source_id or lead.source_id.id != creation_ce_source_id:
                raise UserError(
                    _("The Source {} of Lead {} do not allow the creation of new Companies").format(lead.source_id.name, lead.name))

            if not lead.community_company_id:
                # Create the new company using very basic starting Data
                company = self.env['res.company'].create(lead._get_company_create_vals())

                # Update Lead & Map Place (if exist) fields accordingly
                lead.community_company_id = company.id
                if lead.team_id and lead.team_type == 'map_place_proposal':
                    lead.team_id.community_company_id = company.id

                # Do post creation specific CCEE tasks
                company._community_post_company_creation_tasks()

        # we need to do this commit before proceed to call KeyCloak API calls to build the related KC realms
        self._cr.commit()

        # build keyKloac realm for each new existing new company
        for lead in self:
            if lead.community_company_id:
                lead.community_company_id._create_keycloak_entities()
                lead.community_company_id._community_post_keycloak_creation_tasks()

    @api.multi
    def _get_company_create_vals(self):
        self.ensure_one()
        m_dict = {m.key: m.value for m in self.form_submission_metadata_ids}

        foundation_date = None
        if m_dict.get('partner_foundation_date',False) and m_dict['partner_foundation_date']:
            date_formats = ['%Y-%m-%d','%d-%m-%Y','%Y/%m/%d','%d/%m/%Y']
            for date_format in date_formats:
                try:
                    foundation_date = datetime.strptime(m_dict['partner_foundation_date'], date_format)
                except:
                    pass
            if not foundation_date:
                raise UserError(
                    _("The Foundation Date value {} have a non valid format. It must be: yyyy-mm-dd or dd-mm-yyyy or yyyy/mm/dd or dd/mm/yyyy").format(m_dict['partner_foundation_date']))

        initial_share_amount = 0.00
        if m_dict.get('partner_initial_share_amount',False) and m_dict['partner_initial_share_amount'] or None:
            try:
                initial_share_amount = float(m_dict['partner_initial_share_amount'])
            except:
                pass

        lang_id = None
        if m_dict.get('partner_language',False) and m_dict['partner_language'] or None:
            lang_id = self.env['res.lang'].search([('code','=',m_dict['partner_language'])],limit=1)


        create_vals = {
                'name': self.name,
                'street': self.street,
                'street2': self.street2,
                'city':self.city,
                'zip': self.zip,
                'state_id': self.state_id.id,
                'country_id': self.country_id.id,
                'website': self.website,
                'phone': self.phone,
                'email': self.email_from or (m_dict.get('contact_email',False) and m_dict['contact_email']) or None,
                'vat': m_dict.get('partner_vat',False) and m_dict['partner_vat'] or None,
                'social_twitter': m_dict.get('partner_twitter',False) and m_dict['partner_twitter'] or None,
                'social_facebook': m_dict.get('partner_facebook',False) and m_dict['partner_facebook'] or None,
                'social_instagram': m_dict.get('partner_instagram',False) and m_dict['partner_instagram'] or None,
                'social_telegram': m_dict.get('partner_telegram',False) and m_dict['partner_telegram'] or None,
                'create_user': True,
                'foundation_date': foundation_date,
                'initial_subscription_share_amount': initial_share_amount,
                'default_lang_id': lang_id and lang_id.id or None,
            }

        return create_vals


    @api.multi
    def _create_keycloak_realm(self):
        for lead in self:
            if not lead.community_company_id:
                raise UserError(
                    _("Unable to create the KeyCloack entities from Lead: {}, because it is not yet related to any Community company").format(lead.name))
            lead.community_company_id._create_keycloak_realm()


    @api.multi
    def _create_community_initial_users(self):
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