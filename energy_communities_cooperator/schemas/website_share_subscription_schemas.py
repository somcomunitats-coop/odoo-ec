from typing import Optional

from pydantic import BaseModel

from odoo.addons.base.models.res_company import ResCompany
from odoo.addons.product.models.product_category import ProductCategory
from odoo.addons.product.models.product_template import ProductTemplate

from enum import Enum

class SubscriptionMode(str, Enum):
    member = "member"
    company_member = "company_member"
    invited = "invited"
    company_invited = "company_invited"
    voluntary = "voluntary"

class MembershipMode(str, Enum):
    cooperator = "member"
    invited = "invited"
    voluntary = "voluntary"

class MembershipMode(str, Enum):
    individual = "individual"
    company = "company"

class FormTypeMode(str, Enum):
    global = "global"
    single = "single"

class WebsiteShareSubscriptionContext(BaseModel):
    membership_mode: MembershipMode
    membertype_mode: MemberTypeMode
    formtype_mode: FormTypeMode
    company: ResCompany
    product_categ: ProductCategory
    product: Optional[ProductTemplate] = None
