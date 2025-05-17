
from odoo import http
from odoo.http import request
from datetime import date
from datetime import datetime
import json, hashlib

class LicenseAPI(http.Controller):

    ###
    def generate_signature(self, payload):
        param_model = request.env['ir.config_parameter'].sudo()
        secret = param_model.get_param('license.api.secret_key', '')
        raw = json.dumps(payload, sort_keys=True) + secret
        return hashlib.sha256(raw.encode()).hexdigest()

    @http.route('/api/license/verify', type='json', auth='public', csrf=False)
    def verify_license(self, **post):
        required_params = ['account', 'password', 'key', 'device_code', 'device_name']
        account = post.get('account')
        password = post.get('password')
        key = post.get('key')
        device_code = post.get('device_code')
        device_name = post.get('device_name')
        mac_address = post.get('mac_address')

        for param in required_params:
            if not post.get(param):
                return {
                    'success': False,
                    'message': f"Missing required fields: {param}"
                }
        License = request.env['license.license'].sudo()
        today = date.today()

        ### Có license trạng thái assigned và chưa có device
        assigned_license = License.search([
            ('account', '=', account), 
            ('password', '=', password), 
            ('key', '=', key), 
            ('state', '=', 'assigned')
        ], limit=1)

        if assigned_license:
            # Gán thông tin thiết bị và kích hoạt license
            assigned_license.write({
                'device_code': device_code,
                'device_name': device_name,
                'mac_address': mac_address,
                'last_verify_date': datetime.now(),
            })
            assigned_license.action_activate()
            license_data = {
                'key': assigned_license.key,
                'device_name': assigned_license.device_name,
                'device_code': assigned_license.device_code,
                'mac_address': assigned_license.mac_address,
                'customer': assigned_license.partner_id.name,
                'start_date': str(assigned_license.date_start),
                'end_date': str(assigned_license.date_end),
                'state': assigned_license.state,
                'last_verify_date': str(assigned_license.last_verify_date),
            }
            return {
                'success': True,
                'message': 'License assigned and activated successfully',
                'license': license_data,
                'signature': self.generate_signature(license_data),
            }

        ### Có license đang active và phải kiểm tra thông tin device
        license_rec = License.search([
            ('account', '=', account), 
            ('password', '=', password), 
            ('key', '=', key), 
            ('device_name', '=', device_name),
            ('device_code', '=', device_code),
            ('state', '=', 'active'),
        ], limit=1)

        if not license_rec:
            return {
                'success': False,
                'message': 'Invalid credentials or license not active'
            }

        if license_rec.date_start and license_rec.date_start > today:
            return {
                'success': False,
                'message': 'License not yet valid',
            }

        if license_rec.date_end and license_rec.date_end < today:
            return {
                'success': False,
                'message': 'License expired',
            }
        ###
        license_rec.write({'last_verify_date': datetime.now()})

        license_data = {
            'key': license_rec.key,
            'device_name': license_rec.device_name,
            'device_code': license_rec.device_code,
            'mac_address': license_rec.mac_address,
            'customer': license_rec.partner_id.name,
            'start_date': str(license_rec.date_start),
            'end_date': str(license_rec.date_end),
            'state': license_rec.state,
            'last_verify_date': str(license_rec.last_verify_date),
        }
        return {
            'success': True,
            'message': 'License is valid',
            'license': license_data,
            'signature': self.generate_signature(license_data),
        }

