from odoo import models, fields, api
from datetime import datetime
import hashlib

class DeviceLicense(models.Model):
    _name = 'device.license'
    _inherit = ['mail.thread']
    _description = 'Device License'
    _order = 'create_date desc'

    name = fields.Char('License Name', required=True, tracking=True)
    key = fields.Char('License Key', required=True, copy=False, tracking=True)
    password = fields.Char('Password', copy=False, tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ], default='new')
    
    create_date = fields.Datetime('Ngày tạo', readonly=True, tracking=True)
    activation_date = fields.Datetime('Ngày kích hoạt', tracking=True)
    expired_date = fields.Date('Ngày hết hạn', tracking=True)
    
    device_code = fields.Char('Mã thiết bị', tracking=True)
    device_name = fields.Char('Tên thiết bị', tracking=True)
    device_info = fields.Text('Thông tin thiết bị', tracking=True)
    
    user_id = fields.Many2one('res.users', string='Người dùng', tracking=True)

    @api.model
    def create(self, vals):
        # Tự động tạo license key nếu chưa có
        if not vals.get('key'):
            vals['key'] = self._generate_license_key(vals.get('device_code'))
        # Mã hóa MD5
        if vals.get('password'):
            vals['password'] = self._md5_hash(vals['password'])
        return super().create(vals)

    def _generate_license_key(self, device_code):
        """Sinh key dựa trên mã thiết bị và thời gian hiện tại"""
        raw = f"{device_code or 'device'}-{datetime.utcnow().isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()
    ### MD5
    def _md5_hash(self, raw_password):
        """Mã hóa mật khẩu bằng MD5"""
        return hashlib.md5(raw_password.encode('utf-8')).hexdigest()
    
    def action_activate(self):
        """Hàm gọi khi kích hoạt license"""
        for record in self:
            if record.state != 'active':
                record.state = 'active'
                record.activation_date = datetime.utcnow()
    ### Action "Generate Password"           
    def action_generate_password(self):
        for record in self:
            # Tạo mật khẩu ngẫu nhiên
            raw = record._generate_random_password()
            # Mã hóa MD5 rồi gán vào field
            record.password = record._md5_hash(raw)
    ### Action "Generate Password"   
    def _generate_random_password(self, length=10):
        import secrets
        return secrets.token_urlsafe(length)[:length]
    ### Không cho xóa nếu đã active
    def unlink(self):
        for record in self:
            if record.state == 'active':
                raise models.ValidationError("Không thể xóa license đang ở trạng thái 'active'.")
        return super().unlink()
