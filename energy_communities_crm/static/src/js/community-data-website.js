var oe_community_data_website = {
    start: function () {
        $(".oe_community_data").each(function () {
            var oe_community_data = this;

            var locale = $(".o_website_form_date_past").data("locale");

            $.datepicker.regional = {
                ca_ES: {
                    monthNamesShort: [
                        "Gen",
                        "Feb",
                        "Mar",
                        "Abr",
                        "Mai",
                        "Jun",
                        "Jul",
                        "Ago",
                        "Set",
                        "Oct",
                        "Nov",
                        "Dec",
                    ],
                },
                es_ES: {
                    monthNamesShort: [
                        "Ene",
                        "Feb",
                        "Mar",
                        "Abr",
                        "May",
                        "Jun",
                        "Jul",
                        "Ago",
                        "Sept",
                        "Oct",
                        "Nov",
                        "Dic",
                    ],
                },
            };

            $.datepicker.setDefaults($.datepicker.regional[locale]);

            $(".o_website_form_date_past").datepicker({
                dateFormat: "dd/mm/yy",
                changeMonth: true,
                changeYear: true,
                maxDate: "today",
                yearRange: "2010:+0",
            });

            $(".form-group-disabled").each(function () {
                $(this).hide();
            });

            var originallyRequired = function (el) {
                var raw = el.getAttribute("data-original-required");
                return raw === "True" || raw === "true" || raw === "1";
            };

            var toggleConditionalControls = function ($field, visible) {
                $field.find("input, select, textarea").each(function () {
                    var $el = $(this);
                    var hasOriginalRequired = this.hasAttribute(
                        "data-original-required"
                    );
                    if (visible) {
                        $el.prop("disabled", false);
                        if (hasOriginalRequired) {
                            $el.prop("required", originallyRequired(this));
                        }
                    } else {
                        $el.prop("disabled", true);
                        if (hasOriginalRequired) {
                            $el.prop("required", false);
                        }
                    }
                });
                if (visible) {
                    $field.fadeIn();
                } else {
                    $field.fadeOut();
                }
            };

            $(".data-trigger").each(function () {
                $(this).on("change", function (e) {
                    var impacted_fields_array = $(this).data("trigger").split(",");
                    for (let i = 0; i < impacted_fields_array.length; i++) {
                        // flag to mark if we display conditional fields or not
                        let condition_satisfied = false;
                        // impacted field is the one that will be displayed or hidden based on it's own condition
                        let impacted_field = $(".field-" + impacted_fields_array[i]);
                        // condition is an array. first element defines field key and second field value condition
                        let showifcondition = impacted_field.data("showif").split(":");
                        // get dom element for the condition_field
                        let showifcondition_fields = showifcondition[0].split(",");
                        for (let i = 0; i < showifcondition_fields.length; i++) {
                            let condition_field = $(
                                ".field-" + showifcondition_fields[i]
                            );
                            // try to see if condition_field is a fieldset
                            let condition_field_fieldset =
                                condition_field.find("fieldset");
                            if (condition_field_fieldset.length > 0) {
                                // if a condition_field is a fieldset iterate trough inputs to see if they're marked and meet condition
                                condition_field_fieldset
                                    .find("input")
                                    .each(function () {
                                        if (
                                            $(this).is(":checked") &&
                                            showifcondition[1]
                                                .split(",")
                                                .includes($(this).attr("id"))
                                        ) {
                                            condition_satisfied = true;
                                        }
                                    });
                            } else {
                                // if a condition_field is not fieldset get the input, it can be of type input or select.
                                let condition_field_input = false;
                                let condition_field_input_input =
                                    condition_field.find("input");
                                if (condition_field_input_input.length > 0) {
                                    condition_field_input = condition_field_input_input;
                                }
                                let condition_field_input_select =
                                    condition_field.find("select");
                                if (condition_field_input_select.length > 0) {
                                    condition_field_input =
                                        condition_field_input_select;
                                }
                                // check if it's a checkbox or radio. if so, check if checked to verify condition
                                let condition_field_type =
                                    condition_field_input.attr("type");
                                if (
                                    condition_field_type == "radio" ||
                                    condition_field_type == "checkbox"
                                ) {
                                    if (condition_field_input.is(":checked")) {
                                        condition_satisfied = true;
                                    }
                                } else {
                                    // if condition_field is a regular input, check condition as a regular text
                                    if (
                                        showifcondition[1]
                                            .split(",")
                                            .includes(condition_field_input.val())
                                    ) {
                                        condition_satisfied = true;
                                    }
                                }
                            }
                        }
                        // Show and enable when the condition matches; hide, disable and
                        // drop required otherwise so hidden controls are not validated.
                        toggleConditionalControls(impacted_field, condition_satisfied);
                    }
                });
            });
            // trigger change on load
            $(".data-trigger").trigger("change");
        });
    },
};
$(document).ready(function () {
    oe_community_data_website.start();
});
