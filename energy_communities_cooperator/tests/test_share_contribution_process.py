from lxml import etree

from odoo.tests import common, tagged

from ..config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
    COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
)
from ..models.product import SHARE_PRICE_SAFE_REQUEST_STATES


@tagged("-at_install", "post_install")
class TestShareContributionProcess(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref(
            "energy_communities.energy_community_company_1_wizard"
        ).new_company_id
        cls.company_b = cls.env.ref(
            "energy_communities.energy_community_company_2_wizard"
        ).new_company_id
        cls.member_categ = cls.env.ref(COOP_SHARE_PRODUCT_CATEG_REF)
        cls.voluntary_categ = cls.env.ref(COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF)
        cls.country = cls.env.ref("base.es")
        cls.lang = cls.env["res.lang"].search([("active", "=", True)], limit=1)

        cls.share_a = cls._create_share(
            cls.company_a,
            "Task 2175 share A",
            "Task 2175 short A",
            "T2175A",
            cls.member_categ,
        )
        cls.share_b = cls._create_share(
            cls.company_b,
            "Task 2175 share B",
            "Task 2175 short B",
            "T2175B",
            cls.member_categ,
        )
        cls.voluntary_a = cls._create_share(
            cls.company_a,
            "Task 2175 voluntary A",
            "Task 2175 voluntary short",
            "T2175V",
            cls.voluntary_categ,
        )

    @classmethod
    def _create_share(cls, company, name, short_name, default_code, categ, **extra):
        values = {
            "name": name,
            "short_name": short_name,
            "default_code": default_code,
            "detailed_type": "service",
            "is_share": True,
            "list_price": 100.0,
            "categ_id": categ.id,
            "company_id": company.id,
            "by_individual": True,
            "by_company": True,
        }
        values.update(extra)
        return cls.env["product.template"].with_company(company).create(values)

    def _draft(self, product, values):
        return product.new(values, origin=product)

    def test_short_name_is_required_for_shares(self):
        view = self.env.ref(
            "energy_communities_cooperator.product_template_short_name_required"
        )
        field_node = etree.fromstring(view.arch).xpath("//field[@name='short_name']")[0]
        self.assertIn("is_share", field_node.get("attrs", ""))
        self.assertIn("required", field_node.get("attrs", ""))

    def test_short_name_warning_for_active_duplicate_in_the_same_company(self):
        # Same record must not warn about itself.
        draft = self._draft(self.share_a, {"short_name": self.share_a.short_name})
        self.assertFalse(draft._onchange_short_name())

        other = self._create_share(
            self.company_a,
            "Task 2175 share A2",
            "Task 2175 other short",
            "T2175A2",
            self.member_categ,
        )
        draft = self._draft(other, {"short_name": self.share_a.short_name})
        warning = draft._onchange_short_name()
        self.assertEqual(
            warning["warning"]["message"],
            "The short name '%s' already exists." % self.share_a.short_name,
        )

    def test_short_name_warning_mentions_archived_contribution(self):
        archived = self._create_share(
            self.company_a,
            "Task 2175 archived",
            "Task 2175 archived short",
            "T2175AR",
            self.member_categ,
            active=False,
        )
        draft = self._draft(self.share_a, {"short_name": archived.short_name})
        warning = draft._onchange_short_name()
        self.assertEqual(
            warning["warning"]["message"],
            "The short name '%s' already exists on an archived contribution."
            % archived.short_name,
        )

        self._create_share(
            self.company_a,
            "Task 2175 active twin",
            archived.short_name,
            "T2175AT",
            self.member_categ,
        )
        warning = draft._onchange_short_name()
        self.assertEqual(
            warning["warning"]["message"],
            "The short name '%s' already exists, including on an archived "
            "contribution." % archived.short_name,
        )

    def test_short_name_warning_ignores_other_company_and_non_shares(self):
        draft = self._draft(self.share_a, {"short_name": self.share_b.short_name})
        self.assertFalse(draft._onchange_short_name())

        service = self.env["product.template"].create(
            {
                "name": "Task 2175 service",
                "short_name": "Task 2175 service short",
                "detailed_type": "service",
                "is_share": False,
                "company_id": self.company_a.id,
            }
        )
        draft = self._draft(self.share_a, {"short_name": service.short_name})
        self.assertFalse(draft._onchange_short_name())
        empty = self._draft(self.share_a, {"short_name": False})
        self.assertFalse(empty._onchange_short_name())

    def test_copy_suffixes_short_name_and_default_code_for_shares(self):
        duplicated = self.share_a.copy()
        self.assertEqual(duplicated.short_name, "%s (copy)" % self.share_a.short_name)
        self.assertEqual(
            duplicated.default_code, "%s (copy)" % self.share_a.default_code
        )
        self.assertTrue(duplicated.is_share)
        self.assertEqual(duplicated.company_id, self.company_a)

        kept = self.share_a.copy(
            default={"short_name": "Explicit short name", "default_code": "EXPLICIT"}
        )
        self.assertEqual(kept.short_name, "Explicit short name")
        self.assertEqual(kept.default_code, "EXPLICIT")

        service = self.env["product.template"].create(
            {
                "name": "Task 2175 service copy",
                "short_name": "Keep me",
                "default_code": "KEEP",
                "detailed_type": "service",
                "is_share": False,
                "company_id": self.company_a.id,
            }
        )
        copied_service = service.copy()
        self.assertEqual(copied_service.short_name, "Keep me")
        self.assertEqual(copied_service.default_code, "KEEP")

    def test_list_price_warning_follows_subscription_request_state(self):
        self.assertEqual(SHARE_PRICE_SAFE_REQUEST_STATES, ("draft", "cancelled"))
        request = self._create_subscription_request(self.share_a, "draft")
        draft = self._draft(self.share_a, {"list_price": 150.0})
        self.assertFalse(draft._onchange_list_price())

        request.state = "cancelled"
        self.assertFalse(draft._onchange_list_price())

        for state in ("blocked", "done", "waiting", "transfer", "paid"):
            request.state = state
            warning = draft._onchange_list_price()
            message = warning["warning"]["message"]
            self.assertIn("ATTENTION:", message)
            self.assertIn("DUPLICATING the contribution", message)
            self.assertIn("ARCHIVE it", message)

        same_price = self._draft(self.share_a, {"list_price": self.share_a.list_price})
        self.assertFalse(same_price._onchange_list_price())

        other_company = self._draft(self.share_b, {"list_price": 150.0})
        self.assertFalse(other_company._onchange_list_price())

        service = self.env["product.template"].create(
            {
                "name": "Task 2175 priced service",
                "detailed_type": "service",
                "is_share": False,
                "list_price": 10.0,
                "company_id": self.company_a.id,
            }
        )
        self.assertFalse(
            self._draft(service, {"list_price": 20.0})._onchange_list_price()
        )

    def test_cooperator_type_selection_is_limited_to_the_current_company(self):
        archived = self._create_share(
            self.company_a,
            "Task 2175 archived type",
            "Archived type",
            "T2175AX",
            self.member_categ,
            active=False,
        )
        partner_a = self.env["res.partner"].with_company(self.company_a)
        partner_b = self.env["res.partner"].with_company(self.company_b)
        selection_a = dict(self._selection(partner_a))
        selection_b = dict(self._selection(partner_b))

        self.assertEqual(selection_a["T2175A"], "Task 2175 short A")
        self.assertEqual(selection_a["T2175V"], "Task 2175 voluntary short")
        self.assertNotIn("T2175B", selection_a)
        self.assertNotIn(archived.default_code, selection_a)
        self.assertEqual(selection_b["T2175B"], "Task 2175 short B")
        self.assertNotIn("T2175A", selection_b)

        membership_model = self.env["cooperative.membership"].with_company(
            self.company_a
        )
        membership_a = dict(self._selection(membership_model))
        self.assertIn("T2175A", membership_a)
        self.assertNotIn("T2175V", membership_a)
        self.assertNotIn("T2175B", membership_a)

    def _selection(self, model):
        return model._fields["cooperator_type"]._description_selection(model.env)

    def _create_subscription_request(self, share, state):
        return (
            self.env["subscription.request"]
            .with_company(share.company_id)
            .with_context(from_form=True)
            .create(
                {
                    "firstname": "Task",
                    "lastname": "2175",
                    "email": "task2175.%s@example.com" % share.id,
                    "vat": "00000000T",
                    "address": "Street 1",
                    "city": "Girona",
                    "zip_code": "17001",
                    "country_id": self.country.id,
                    "lang": self.lang.code,
                    "ordered_parts": 1,
                    "share_product_id": share.product_variant_id.id,
                    "company_id": share.company_id.id,
                    "is_operation": True,
                    "state": state,
                }
            )
        )
