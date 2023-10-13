odoo.define('hrm.hide_button_edit', function (require) {
"use strict";
    console.log('hide_button_edit');
    var FormController = require('web.FormController');
    var viewRegistry = require('web.view_registry');
    var FormView = require('web.FormView');
    var MyFormController = FormController.extend({
        _updateButtons: function () {
            this._super.apply(this, arguments);
            console.log('button' + this.renderer.state.data.state);
            console.log('button 2 ' + this.$buttons);
            if (this.$buttons) {
                if (this.renderer.state.data.state !== 'draft'){
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