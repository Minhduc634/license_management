{
    'name': 'License Management',
    'version': '1.0',
    'category': 'License',
    'depends': ['base', 'mail'],
    'data': [   
        'security/ir.model.access.csv',
        'views/license_views.xml',
    ],     
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}


