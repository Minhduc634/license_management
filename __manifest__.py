{
    'name': 'License Management',
    'version': '1.0',
    'category': 'License',
    'depends': ['base', 'mail', "product"],
    'data': [   
        'security/ir.model.access.csv',
        'views/license_views.xml',
        'data/ir_sequence.xml',
    ],     
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}


