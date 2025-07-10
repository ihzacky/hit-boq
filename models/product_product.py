from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    work_unit_material_line_ids = fields.One2many(
        'boq.material.line',
        'product_id',
        string='BOQ Material Lines'
    )

    work_unit_service_line_ids = fields.One2many(
        'boq.service.line',
        'product_id',
        string='BOQ Service Lines'
    )

    work_unit_count = fields.Integer(
        string='Work Unit Count',
        compute='_compute_work_unit_count',
        store=False
    )

    @api.depends('work_unit_material_line_ids', 'work_unit_service_line_ids')
    def _compute_work_unit_count(self):
        for product in self:
            material_work_units = product.work_unit_material_line_ids.mapped('work_unit_id')
            service_work_units = product.work_unit_service_line_ids.mapped('work_unit_id')
            all_work_units = material_work_units | service_work_units
            
            active_work_units = all_work_units.filtered(lambda w: not w.is_duplicate)
            product.work_unit_count = len(active_work_units)

    def action_view_work_units(self):
        self.ensure_one()
        work_units = self.env['boq.work_unit']
        if self.work_unit_material_line_ids:
            work_units |= self.work_unit_material_line_ids.mapped('work_unit_id')
        if self.work_unit_service_line_ids:
            work_units |= self.work_unit_service_line_ids.mapped('work_unit_id')

        return {
            'name': 'Satuan Pekerjaan',
            'type': 'ir.actions.act_window',
            'res_model': 'boq.work_unit',
            'view_mode': 'tree,form',
            'domain': [
                ('id', 'in', work_units.ids),
                ('is_duplicate', '=', False)

            ],
            'target': 'current',
        }