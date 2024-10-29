var oe_website_data = {
  onGroupDisable: function (class_group) {
    $(class_group).each(function () {
      $(this).hide();
    });
  },
  OnDatePicker: function (locale, field) {
    var locale = $(locale).data("locale");

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

    $(field).datepicker({
      dateFormat: "dd/mm/yy",
      changeMonth: true,
      changeYear: true,
      maxDate: "today",
      yearRange: "2010:+0",
    });
  },
};
