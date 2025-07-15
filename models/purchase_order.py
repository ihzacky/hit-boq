from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    work_unit_id = fields.Many2one(
        'boq.work_unit',
        string='Work Unit',
        compute='_compute_work_unit_id',
        store=True,
        help='Work Unit related to this purchase order'
    )
    
    @api.depends('origin')
    def _compute_work_unit_id(self):
        for record in self:
            work_unit = None
            if record.origin:
                # Try to find work unit by origin pattern
                # Origin format should be: "WORK_UNIT_CODE - WORK_UNIT_NAME"
                work_unit_code = record.origin.split(' - ')[0] if ' - ' in record.origin else record.origin
                work_unit = self.env['boq.work_unit'].search([('code', '=', work_unit_code)], limit=1)
            record.work_unit_id = work_unit.id if work_unit else False
