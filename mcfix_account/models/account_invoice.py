from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.onchange('company_id')
    def onchange_company_id(self):
        for invoice in self:
            invoice.journal_id = self.env['account.journal'].search(
                [('company_id', '=', invoice.company_id.id),
                 ('type', '=', invoice.journal_id.type)
                 ], limit=1)
            for line in invoice.invoice_line_ids:
                line.change_company_id()
        return {}

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        addr = self.partner_id.address_get(['delivery'])
        self.fiscal_position_id = \
            self.env['account.fiscal.position'].with_context(
            force_company=self.company_id.id).get_fiscal_position(
                self.partner_id.id, delivery_id=addr['delivery'])


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.v8
    def get_invoice_line_account(self, type, product, fpos, company):
        return super(AccountInvoiceLine, self.with_context(
            force_company=company.id)).get_invoice_line_account(
            type, product, fpos, company)

    @api.model
    def change_company_id(self):
        part = self.invoice_id.partner_id
        type = self.invoice_id.type
        company = self.invoice_id.company_id.id
        if part.lang:
            product = self.product_id.with_context(lang=part.lang)
        else:
            product = self.product_id
        account = self.get_invoice_line_account(
            type,
            product.with_context(force_company=company),
            self.invoice_id.fiscal_position_id,
            self.invoice_id.company_id)
        if account:
            self.account_id = account.id
        self._set_taxes()
