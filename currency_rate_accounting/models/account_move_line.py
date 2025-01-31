from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    def _is_currency_rate_enabled(self):
        return self.env['ir.config_parameter'].sudo().get_param('currency_rate_accounting.enabled', False)
        
    currency_rate_enabled = fields.Boolean(
        string='Currency Rate Enabled',
        compute='_compute_currency_rate_enabled',
    )
    
    usd_rate = fields.Float(
        string='USD Rate',
        digits=(12, 6),
        readonly=True,
        related='move_id.usd_rate',
        store=True,
        help='USD exchange rate for the entry date'
    )
    
    credito_usd = fields.Float(
        string='Credito USD',
        compute='_compute_credito_debito_usd',
        store=True
    )
    
    debito_usd = fields.Float(
        string='Debito USD',
        compute='_compute_credito_debito_usd',
        store=True
    )
    
    balance_usd = fields.Float(
        string='Balance USD',
        compute='_compute_balance_usd',
        store=True
    )

    @api.model
    def _get_field_dependencies(self):
        dep = super()._get_field_dependencies()
        dep.update({
            'credito_usd': ['credit', 'move_id.usd_rate'],
            'debito_usd': ['debit', 'move_id.usd_rate'],
            'balance_usd': ['debito_usd', 'credito_usd'],
        })
        return dep
        
    @api.depends('move_id')
    def _compute_currency_rate_enabled(self):
        enabled = self._is_currency_rate_enabled()
        for record in self:
            record.currency_rate_enabled = enabled

    @api.depends('credit', 'debit', 'move_id.usd_rate')
    def _compute_credito_debito_usd(self):
        for line in self:
            if not line._is_currency_rate_enabled():
                line.credito_usd = 0.0
                line.debito_usd = 0.0
                continue

            # Obtener la tasa del contexto si existe, sino usar la del asiento
            rate = self.env.context.get('force_rate', line.usd_rate)
            
            if rate:
                # Si la tasa es 500 ARS = 1 USD y tenemos 1000 ARS:
                # 1000 ARS * (1/500) = 2 USD
                factor = 1.0 / rate if rate else 0.0
                line.credito_usd = line.credit * factor if line.credit else 0.0
                line.debito_usd = line.debit * factor if line.debit else 0.0
            else:
                line.credito_usd = 0.0
                line.debito_usd = 0.0

    @api.depends('debito_usd', 'credito_usd')
    def _compute_balance_usd(self):
        for line in self:
            if not line._is_currency_rate_enabled():
                line.balance_usd = 0.0
                continue
                
            line.balance_usd = line.debito_usd - line.credito_usd
