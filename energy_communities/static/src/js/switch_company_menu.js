/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {browser} from "@web/core/browser/browser";
import {useState} from "@odoo/owl";

import {SwitchCompanyMenu} from "@web/webclient/switch_company_menu/switch_company_menu";

patch(SwitchCompanyMenu.prototype, "SwitchCompanyMenuCustom", {
  setup() {
    this._super(...arguments);
    this.state = useState({
      companiesToToggle: [],
      searchTerm: "",
      filteredCompanies: Object.values(this.companyService.availableCompanies).sort(
        (c1, c2) => c1.sequence - c2.sequence
      ),
    });
  },

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

  /**
   * Update filtered companies based on search term
   */
  updateFilteredCompanies() {
    const allCompanies = Object.values(this.companyService.availableCompanies);
    const searchTerm = this.state.searchTerm.toLowerCase().trim();

    if (searchTerm === "") {
      // Show all companies when search is empty
      this.state.filteredCompanies = allCompanies.sort(
        (c1, c2) => c1.sequence - c2.sequence
      );
    } else {
      // Filter companies based on search term
      this.state.filteredCompanies = allCompanies
        .filter((company) => company.name.toLowerCase().includes(searchTerm))
        .sort((c1, c2) => c1.sequence - c2.sequence);
    }
  },

  /**
   * Clear search term
   */
  clearSearch() {
    this.state.searchTerm = "";

    // Clear timeout if exists
    if (this.searchTimeout) {
      browser.clearTimeout(this.searchTimeout);
    }

    // Immediately update to show all companies
    this.updateFilteredCompanies();
  },

  /**
   * Update search term with debounce
   */
  onSearchInput(event) {
    this.state.searchTerm = event.target.value;

    // Clear previous timeout
    if (this.searchTimeout) {
      browser.clearTimeout(this.searchTimeout);
    }

    // Set new timeout for debounced search
    this.searchTimeout = browser.setTimeout(() => {
      this.updateFilteredCompanies();
    }, 300); // 300ms delay
  },
});

export default SwitchCompanyMenu;
