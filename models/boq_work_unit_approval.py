from odoo import models, fields, api


class BoqWorkUnitApproval(models.Model):
    _inherit = "boq.work_unit"

    current_assigned_to = fields.Many2one(comodel_name="res.users", string="Approver", tracking=True, index=True, readonly=True)
    release_strategy_ids = fields.One2many("approval.release.strategy", "obj_id", string="Release Strategy", domain=lambda self: [("model", "=", self._name)])
    show_button_approve = fields.Boolean(compute="get_show_button", string="Show Button Approve")
    current_assigned_to_ids = fields.Many2many(
        string="Approver Ids",
        comodel_name="res.users",
        relation="rel_boq_work_unit_approver",
        column1="boq_work_unit_id",
        column2="user_id",
    )

    def get_show_button(self):
        self.show_button_approve = False
        self.show_button_approve = self.release_strategy_ids.get_show_button(self._name, self.id, "to_approve")

    def set_draft(self):
        return self.write({"state": "draft"})

    def set_to_approve(self):
        return self.write({"state": "to_approve"})
    
    def set_approved(self):
        return self.write({"state": "approved"})

    def set_rejected(self):
        return self.write({"state": "rejected"})


    # -------------------------------------------------------------
    
    def button_to_approve(self):
        self.release_strategy_ids.button_approve(self._name, self.id, "set_to_approve", "set_approved")
        return True

    def button_to_reject(self):
        # self._check_rejected_note()
        self.release_strategy_ids.button_reject(self._name, self.id, "set_rejected")
        return True

    def button_to_revision(self):
        self.release_strategy_ids.button_draft(self._name, self.id, "set_draft")
        return True

    def button_request_approval(self):
        # self._check_quantity()
        self.release_strategy_ids.generate_release_strategy(self._name, self.id, "set_to_approve", self.name)
        return True 


