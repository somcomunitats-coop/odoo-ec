/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {MonetaryField} from "@web/views/fields/monetary/monetary_field";

import {onWillUpdateProps} from "@odoo/owl";

const PRICE_EPSILON = 0.0000001;

export class SharePriceMonetaryField extends MonetaryField {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.lastCommittedPrice = this.props.value;
        this.ignoreNextPriceChange = false;
        this.confirmationTarget = undefined;
        this.priceChangeToken = 0;
        onWillUpdateProps((nextProps) => this.onPricePropsUpdate(nextProps));
    }

    pricesDiffer(left, right) {
        return Math.abs((left || 0) - (right || 0)) > PRICE_EPSILON;
    }

    async onPricePropsUpdate(nextProps) {
        if (this.ignoreNextPriceChange) {
            this.ignoreNextPriceChange = false;
            this.lastCommittedPrice = nextProps.value;
            this.confirmationTarget = undefined;
            return;
        }
        if (!this.pricesDiffer(this.lastCommittedPrice, nextProps.value)) {
            return;
        }
        if (
            this.confirmationTarget !== undefined &&
            !this.pricesDiffer(this.confirmationTarget, nextProps.value)
        ) {
            return;
        }
        if (nextProps.readonly || !this.props.record.resId) {
            this.lastCommittedPrice = nextProps.value;
            return;
        }
        const token = ++this.priceChangeToken;
        this.confirmationTarget = nextProps.value;
        const payload = await this.orm.call(
            "product.template",
            "get_share_price_change_confirmation",
            [[this.props.record.resId], nextProps.value]
        );
        if (token !== this.priceChangeToken) {
            return;
        }
        if (!payload) {
            this.lastCommittedPrice = nextProps.value;
            this.confirmationTarget = undefined;
            return;
        }
        const previousPrice = this.lastCommittedPrice;
        this.dialog.add(ConfirmationDialog, {
            title: payload.title,
            body: payload.message,
            confirmLabel: payload.confirm_label,
            cancelLabel: payload.cancel_label,
            confirm: () => {
                this.lastCommittedPrice = nextProps.value;
                this.confirmationTarget = undefined;
            },
            cancel: async () => {
                this.ignoreNextPriceChange = true;
                this.confirmationTarget = undefined;
                await this.props.update(previousPrice);
            },
        });
    }
}

SharePriceMonetaryField.template = "web.MonetaryField";
SharePriceMonetaryField.supportedTypes = ["monetary", "float"];

registry.category("fields").add("share_price_monetary", SharePriceMonetaryField);
