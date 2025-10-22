/** @odoo-module **/

import {patch} from "@web/core/utils/patch";

import {SwitchCompanyMenu} from "@web/webclient/switch_company_menu/switch_company_menu";

patch(SwitchCompanyMenu.prototype, "SwitchCompanyMenuCustom", {
  /**
   * Toggle all companies at once
   * @param {boolean} selectAll - true to select all, false to deselect all
   */
  toggleAllCompanies(selectAll) {
    const allCompanyIds = Object.keys(this.companyService.availableCompanies).map(
      (id) => parseInt(id)
    );
    const currentSelectedIds = this.companyService.allowedCompanyIds;

    if (selectAll) {
      // Select all companies that are not currently selected
      const companiesToSelect = allCompanyIds.filter(
        (id) => !currentSelectedIds.includes(id)
      );
      if (companiesToSelect.length > 0) {
        this.companyService.setCompanies("toggle", ...companiesToSelect);
      }
    } else {
      // Deselect all companies except the current one
      const companiesToDeselect = currentSelectedIds.filter(
        (id) => id !== this.companyService.currentCompany.id
      );
      if (companiesToDeselect.length > 0) {
        this.companyService.setCompanies("toggle", ...companiesToDeselect);
      }
    }
  },

  /**
   * Check if all companies are currently selected
   */
  areAllCompaniesSelected() {
    const allCompanyIds = Object.keys(this.companyService.availableCompanies).map(
      (id) => parseInt(id)
    );
    const currentSelectedIds = this.companyService.allowedCompanyIds;
    return allCompanyIds.every((id) => currentSelectedIds.includes(id));
  },

  /**
   * Check if no companies are selected (except current)
   */
  areNoCompaniesSelected() {
    const currentSelectedIds = this.companyService.allowedCompanyIds;
    return currentSelectedIds.length <= 1; // Only current company selected
  },
});

export default SwitchCompanyMenu;
