from odoo import http
from odoo.http import request
from datetime import date
class LicenseAPI(http.Controller):

    @http.route('/license/verify', type='json', auth='public', methods=['POST'], csrf=False)
    def verify_license(self, device_id=None, license_key=None):
        license = request.env['license.license'].sudo().search([
            ('device_id', '=', device_id),
            ('license_key', '=', license_key)
        ], limit=1)

        if not license:
            return {'valid': False, 'error': 'License not found'}

        if license.status != 'active':
            return {'valid': False, 'error': 'License not active'}

        if license.expiration_date and license.expiration_date < date.today():
            return {'valid': False, 'error': 'License expired'}

        return {
            'valid': True,
            'expires': str(license.expiration_date),
            'status': license.status,
        }
