odoo.define('hrm.hrm_employee_profile', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var viewRegistry = require('web.view_registry');
    var FormView = require('web.FormView');

    var MyFormController = FormController.extend({
        _updateButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                // Lấy trạng thái dữ liệu từ renderer
                var dataState = this.renderer.state.data.state;

                // Kiểm tra trạng thái dữ liệu và ẩn nút "Edit" nếu cần
                if (dataState !== 'draft') {
                    this.$buttons.find('.o_form_button_edit').hide();
                } else {
                    this.$buttons.find('.o_form_button_edit').show();
                }
            }
        },
    });

    var MyFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: MyFormController,
        }),
    });

    viewRegistry.add('custom_form', MyFormView);
});
