from odoo import models, fields, api

class AccountMove(models.Model):
   _inherit = 'account.move'
   
   def _is_currency_rate_enabled(self):
       return self.env['ir.config_parameter'].sudo().get_param('currency_rate_accounting.enabled', False)

   usd_rate = fields.Float(
       string='USD Rate',
       digits=(12, 6),
       readonly=True,
       compute='_compute_usd_rate',
       store=True,
       help='USD exchange rate for the entry date'
   )
   
   rate_date = fields.Date(
       string='Rate Date',
       help='Date of the exchange rate applied'
   )

   @api.depends('date')
   def _compute_usd_rate(self):
       for move in self:
           if not self._is_currency_rate_enabled():
               move.usd_rate = 1.0
               continue

           # Obtener la moneda USD
           usd_currency = self.env.ref('base.USD')
           if not usd_currency:
               move.usd_rate = 1.0
               continue
               
           # Usar tasa forzada del contexto si existe
           forced_rate = self.env.context.get('force_rate', False)
           if forced_rate:
               move.usd_rate = forced_rate
               continue
               
           # Buscar la tasa histórica más cercana anterior
           nearest_rate = self.env['res.currency.rate'].search([
               ('currency_id', '=', usd_currency.id),
               ('company_id', '=', move.company_id.id),
               ('name', '<=', move.date)
           ], limit=1, order='name desc')
           
           if nearest_rate:
               # Guardamos la tasa directa (si 1 USD = 500 ARS, guardamos 500)
               move.usd_rate = 1 / nearest_rate.rate if nearest_rate.rate else 1.0
               move.rate_date = nearest_rate.name
           else:
               # Si no hay tasa anterior, buscar la siguiente más cercana
               next_rate = self.env['res.currency.rate'].search([
                   ('currency_id', '=', usd_currency.id),
                   ('company_id', '=', move.company_id.id),
                   ('name', '>', move.date)
               ], limit=1, order='name asc')
               
               if next_rate:
                   move.usd_rate = 1 / next_rate.rate if next_rate.rate else 1.0
                   move.rate_date = next_rate.name
               else:
                   move.usd_rate = 1.0
                   move.rate_date = False

   def action_open_currency_rate(self):
       """Abre la vista para editar la tasa de cambio"""
       if not self._is_currency_rate_enabled():
           return False
           
       self.ensure_one()
       # Obtener la moneda USD
       usd_currency = self.env.ref('base.USD')
       if not usd_currency:
           return False

       # Buscar la tasa para la fecha del asiento
       rate = self.env['res.currency.rate'].search([
           ('currency_id', '=', usd_currency.id),
           ('company_id', '=', self.company_id.id),
           ('name', '=', self.date)
       ], limit=1)
       
       if not rate:
           # Si no existe la tasa para esta fecha, crear una nueva
           # Convertimos la tasa directa a inversa para guardarla
           rate = self.env['res.currency.rate'].create({
               'currency_id': usd_currency.id,
               'company_id': self.company_id.id,
               'name': self.date,
               'rate': 1 / self.usd_rate if self.usd_rate else 1.0,  # Convertir a tasa inversa
           })
       
       return {
           'name': 'Tasa de Cambio USD',
           'view_mode': 'form',
           'res_model': 'res.currency.rate',
           'res_id': rate.id,
           'type': 'ir.actions.act_window',
           'target': 'new',
           'context': {
               'default_rate': 1 / self.usd_rate if self.usd_rate else 1.0  # Convertir a tasa inversa
           }
       }
