# -*- coding: utf-8 -*-
{
    'name': "hrm",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'application': True,
    'sequence': -100,
    # any module necessary for this one to work correctly
    'depends': ['base', 'utm', 'mail'],

    # always loaded
    'data': [
        'views/blocks_view.xml',
<<<<<<< HEAD
        'views/menu.xml',
        # 'views/hrm_position_view'
=======
        'views/employee_profile_view.xml',
        'views/menu.xml'
>>>>>>> 5ab18f2be80dd364744331de0affafd11a59956b
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
