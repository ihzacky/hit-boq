from odoo import models, fields

class BoqRoot(models.Model):
    _name = 'boq.root'
    _description = 'BoQ Root'


    boq_code = fields.Char(string='Kode BoQ')
    boq_name = fields.Char(string='Nama')
    material_margin = fields.Float(string='Material Margin')
    installation_margin = fields.Float(string='Installation Margin')
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")

    price_final = fields.Monetary(string='Total Harga', currency_field='currency_id')

    # tambahin status

    work_unit_id = fields.Many2many(
        comodel_name='boq.work_unit',
        string='Work Unit Root'
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )
    

    
    