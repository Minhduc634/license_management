import uuid
import re
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import date_utils

class License(models.Model):
    _name = 'license.license'
    _description = 'License'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    key = fields.Char(
        string='License Key',
        required=True,
        readonly=True,
        default=lambda self: str(uuid.uuid4()).upper(),
        tracking=True,
    )

    device_code = fields.Char(string='Device Code', tracking=True)
    device_name = fields.Char(string='Device Name', tracking=True)
    password = fields.Char(string='Password', tracking=True)

    type_id = fields.Many2one(
        'license.type',
        string='Type',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        readonly=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('assigned', 'Ready'),
            ('active', 'Active'),
            ('disabled', 'Disabled'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )
    date_start = fields.Date(string='Start Date', tracking=True)
    runtime = fields.Float(string='Runtime (Months)', default=12)
    date_end = fields.Date(
        string='End Date',
        compute='_compute_date_end',
        inverse='_inverse_date_end',
        store=True,
        tracking=True,
    )

    @api.constrains('password')
    def _check_complex_password(self):
        
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
        for rec in self:
            if rec.password and not re.match(pattern, rec.password):
                raise UserError(_(
                    "Mật khẩu phải dài ít nhất 8 ký tự và bao gồm "
                    "ít nhất một chữ cái viết hoa, một chữ cái viết thường, một số, "
                    "và một ký tự đặc biệt."
                ))

    @api.depends('date_start', 'runtime')
    def _compute_date_end(self):
        for rec in self:
            rec.date_end = (
                date_utils.add(rec.date_start, months=rec.runtime)
                if rec.date_start else False
            )

    def _inverse_date_end(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                diff = date_utils.diff(rec.date_end, rec.date_start)
                # Chuyển đổi thành tháng (xấp xỉ ngày thành phần)
                rec.runtime = diff.years * 12 + diff.months + diff.days / 30.0
            else:
                rec.runtime = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Gán sequence cho name
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('license.license') or _('New')
            # Gán UUID cho key nếu chưa có
            vals.setdefault('key', str(uuid.uuid4()).upper())
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault(
            'name',
            self.env['ir.sequence'].next_by_code('license.license') or _('New')
        )
        default.setdefault('key', str(uuid.uuid4()).upper())
        return super().copy(default)

    def action_assign(self):
        return self.write({'state': 'assigned'})

    def action_activate(self):
        today = fields.Date.context_today(self)
        return self.write({
            'state': 'active',
            'date_start': self.date_start or today,
        })

    def action_reset(self):
        return self.write({'state': 'assigned', 'date_start': False, 'date_end': False})

    def action_disable(self):
        today = fields.Date.context_today(self)
        return self.write({'state': 'disabled', 'date_end': today})

    def action_enable(self):
        today = fields.Date.context_today(self)
        return self.write({
            'state': 'active',
            'date_start': self.date_start or today,
        })

    def action_cancel(self):
        today = fields.Date.context_today(self)
        return self.write({'state': 'cancelled', 'date_end': today})

    def action_draft(self):
        return self.write({'state': 'draft', 'date_start': False, 'date_end': False})

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancelled'):
                raise UserError(_('You cannot delete a license unless it is Draft or Cancelled.'))
        return super().unlink()
