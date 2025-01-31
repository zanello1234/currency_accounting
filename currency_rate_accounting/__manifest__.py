##############################################################################
#
#    Copyright (C) 2024  Only-One Odoo  (https://www.onlyone.odoo.com)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Currency Rate Accounting',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': 'Ver todas las entradas convertidas a dólares',
    'author': 'Only-One Odoo',
    'website': 'https://www.onlyone.odoo.com',
    'license': 'LGPL-3',
    'images': [
    ],
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'views/account_move_views.xml',
        'views/account_move_lines_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
