{
    'name': "hrm",

    'summary': """
        Quản lý thông tin nhân viên.
    """,

    'description': """
        Long description of module's purpose
    """,

    'author': "TTS Big Holding",
    'website': "http://dev.obd.life/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',
    'application': True,
    'sequence': -100,
    # any module necessary for this one to work correctly
    'depends': ['base','utm', 'mail'],

    # always loaded
    'data': [
        'wizard/approval_reason_refusal.xml',

        'views/blocks_view.xml',
        'data/blocks_data.xml',
        'views/systems_views.xml',
        'views/departments_view.xml',
        'views/companies_view.xml',
        'views/position_view.xml',
        'views/employee_profile_view.xml',
        'views/approval_view.xml',
        'views/approval_flow_config.xml',
        'views/menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'css': [
        'static/src/css/style.css',
    ],
}
# -*- coding: utf-8 -*-
