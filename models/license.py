
import uuid
import re, random, string
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class License(models.Model):
    _name = 'license.license'
    _description = 'License'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    _sql_constraints = [
        ('key_uniq', 'UNIQUE (key)', 'Key is duplicated !')
    ]

    name = fields.Char(
        string='Reference ',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    key = fields.Char(
        default=lambda self: _("New"),
        compute="_compute_key",
        tracking=True,
        required=True,
        store=True,
        # states={"draft": [("readonly", False)]},
    )

    device_code = fields.Char(string='Device Code ', tracking=True)
    device_name = fields.Char(string='Device Name ', tracking=True)
    ###
    mac_address = fields.Char(string='MAC Address', tracking=True)
    last_verify_date = fields.Datetime(string='Last Verify Time', tracking=True)
    ###
    account = fields.Char(string='Account', required=True, tracking=True)
    password = fields.Char(string='Password ', tracking=True, required=True, default=lambda self: self.generate_strong_password())

    type_id = fields.Many2one(
        'license.type',
        string='Type',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer ',
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
    # date_start = fields.Date(string='Start Date', tracking=True)
    date_start = fields.Date(
        string='Start Date', 
        tracking=True,
    )

    # runtime = fields.Float(string='Runtime (Months) ', default=12)
    runtime = fields.Float(
        string='Runtime (Months)',
        default=12, 
    )

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

    def generate_strong_password(self, length=12):
        if length < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        lowercase = random.choice(string.ascii_lowercase)
        uppercase = random.choice(string.ascii_uppercase)
        digit = random.choice(string.digits)
        special = random.choice("!@#$%^&*()-_=+[]{}|;:,.<>?")

        others = ''.join(random.choices(
            string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?",
            k=length - 4
        ))

        password = list(lowercase + uppercase + digit + special + others)
        random.shuffle(password)
        return ''.join(password)
 
    @api.depends('date_start', 'runtime')
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start and rec.runtime:
                months = int(rec.runtime)
                days = int((rec.runtime - months) * 30)
                rec.date_end = rec.date_start + relativedelta(months=months, days=days)
            else:
                rec.date_end = False

    def _inverse_date_end(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                delta = relativedelta(rec.date_end, rec.date_start)
                rec.runtime = delta.years * 12 + delta.months + delta.days / 30.0
            else:
                rec.runtime = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Gán sequence cho name
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('license.license') or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault(
            'name',
            self.env['ir.sequence'].next_by_code('license.license') or _('New')
        )
        return super().copy(default)

    @api.depends("create_date")
    def _compute_key(self):
        for license in self.filtered(lambda r: r.key == _("New")):
            license.key = str(uuid.uuid4()).upper()

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
