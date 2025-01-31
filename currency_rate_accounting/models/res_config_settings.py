from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
   _inherit = 'res.config.settings'
   
   currency_rate_accounting_enabled = fields.Boolean(
       string='Habilitar Currency Rate Accounting', 
       config_parameter='currency_rate_accounting.enabled'
   )

   def recalculate_usd_amounts(self):
       self.ensure_one()
       if not self.currency_rate_accounting_enabled:
           return False

       # Obtener la moneda USD
       usd_currency = self.env.ref('base.USD')
       if not usd_currency:
           return False

       # Obtener todas las líneas de asiento
       move_lines = self.env['account.move.line'].search([], order='date')

       dates_processed = set()
       rates_cache = {}
       lines_updated = 0
       moves_updated = set()

       for line in move_lines:
           date = line.move_id.date
           company = line.company_id
           move = line.move_id

           # Cachear la tasa por fecha y compañía
           cache_key = (date, company.id)
           
           if cache_key not in rates_cache:
               # Buscar la tasa más cercana anterior
               nearest_rate = self.env['res.currency.rate'].search([
                   ('currency_id', '=', usd_currency.id),
                   ('company_id', '=', company.id),
                   ('name', '<=', date)
               ], limit=1, order='name desc')

               if nearest_rate:
                   # Guardamos la tasa directa (si 1 USD = 500 ARS, guardamos 500)
                   rates_cache[cache_key] = {
                       'rate': 1 / nearest_rate.rate if nearest_rate.rate else 1.0,
                       'date': nearest_rate.name
                   }
                   dates_processed.add(date)
               else:
                   # Si no hay tasa anterior, buscar la siguiente más cercana
                   next_rate = self.env['res.currency.rate'].search([
                       ('currency_id', '=', usd_currency.id),
                       ('company_id', '=', company.id),
                       ('name', '>', date)
                   ], limit=1, order='name asc')
                   if next_rate:
                       rates_cache[cache_key] = {
                           'rate': 1 / next_rate.rate if next_rate.rate else 1.0,
                           'date': next_rate.name
                       }
                   else:
                       rates_cache[cache_key] = {
                           'rate': 1.0, 
                           'date': False
                       }

           rate_info = rates_cache[cache_key]
           
           # Actualizar el asiento con la tasa si no se ha actualizado antes
           if move.id not in moves_updated:
               move.write({
                   'usd_rate': rate_info['rate'],
                   'rate_date': rate_info['date']
               })
               moves_updated.add(move.id)

           # Forzar el recálculo de los campos USD usando el contexto
           line.with_context(force_rate=rate_info['rate'])._compute_credito_debito_usd()
           line._compute_balance_usd()
           
           lines_updated += 1

       message = f'Recálculo completado:\n'
       message += f'- Líneas procesadas: {lines_updated}\n'
       message += f'- Asientos actualizados: {len(moves_updated)}\n'
       message += f'- Fechas distintas: {len(dates_processed)}'
       
       return {
           'type': 'ir.actions.client',
           'tag': 'display_notification',
           'params': {
               'title': 'Recálculo Completado',
               'message': message,
               'type': 'success',
               'sticky': False,
           }
       }
