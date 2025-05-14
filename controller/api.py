from odoo import http
from odoo.http import request
from datetime import date
class LicenseAPI(http.Controller):

    @http.route('/api/license/verify', type='json', auth='public', csrf=False)
    def verify_license(self, **post):
        license_key = post.get('license_key')
        device_code = post.get('device_code')
        password = post.get('password')

        if not license_key or not device_code or not password:
            return {
                'success': False,
                'message': 'Missing required fields: license_key, device_code, password'
            }

        License = request.env['license.license'].sudo()
        license_rec = License.search([
            ('key', '=', license_key),
            ('device_code', '=', device_code),
            ('password', '=', password),
            ('state', '=', 'active')
        ], limit=1)

        if not license_rec:
            return {
                'success': False,
                'message': 'Invalid credentials or license not active'
            }

        today = date.today()
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

        return {
            'success': True,
            'message': 'License is valid',
            'license': {
                'key': license_rec.key,
                'device_name': license_rec.device_name,
                'customer': license_rec.partner_id.name,
                'start_date': str(license_rec.date_start),
                'end_date': str(license_rec.date_end),
                'runtime_months': license_rec.runtime,
                'state': license_rec.state,
            }
        }