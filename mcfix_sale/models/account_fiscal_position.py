# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    @api.constrains('company_id')
    def _check_company_id(self):
        super(AccountFiscalPosition, self)._check_company_id()
        for rec in self:
            order = self.env['sale.order'].search(
                [('fiscal_position_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if order:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Fiscal Position is assigned to Sales Order '
                      '%s.' % order.name))
