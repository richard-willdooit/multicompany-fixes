# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    invoice_ids = fields.One2many(comodel_name='account.invoice',
                                  inverse_name='journal_id', string='Invoices')

    @api.multi
    @api.depends('name', 'currency_id', 'company_id', 'company_id.currency_id')
    def name_get(self):
        res = []
        journal_names = super(AccountJournal, self).name_get()
        multicompany_group = self.env.ref('base.group_multi_company')
        if multicompany_group not in self.env.user.groups_id:
            return journal_names
        for journal_name in journal_names:
            journal = self.browse(journal_name[0])
            name = "%s [%s]" % (
                journal_name[1], journal.company_id.name) if \
                journal.company_id else journal_name[1]
            res += [(journal.id, name)]
        return res

    @api.multi
    @api.depends('company_id')
    def _belong_to_company_or_child(self):
        for journal in self:
            journal.belong_to_company_or_child = len(self.search(
                [('company_id', 'child_of', self.env.user.company_id.id)])) > 0

    @api.multi
    def _search_user_company_and_child_journals(self, operator, value):
        companies = self.env.user.company_id + \
            self.env.user.company_id.child_ids
        if operator == '=':
            recs = self.search([('company_id', 'in', companies.ids)])
        elif operator == '!=':
            recs = self.search([('company_id', 'not in', companies.ids)])
        else:
            raise UserError(_("Invalid search operator."))

        return [('id', 'in', [x.id for x in recs])]

    belong_to_company_or_child = fields.Boolean(
        'Belong to the user\'s current child company',
        compute="_belong_to_company_or_child",
        search="_search_user_company_and_child_journals")

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.invoice_ids = False
        self.account_control_ids = False
        self.profit_account_id = False
        self.loss_account_id = False

    @api.multi
    @api.constrains('invoice_ids', 'company_id')
    def _check_company_invoice_ids(self):
        for journal in self.sudo():
            for invoice in journal.invoice_ids:
                if journal.company_id and invoice.company_id and \
                        journal.company_id != invoice.company_id:
                    raise ValidationError(
                        _('The Company in the Journal and in Invoice %s '
                          'must be the same.') % invoice.name)
        return True

    @api.multi
    @api.constrains('account_control_ids', 'company_id')
    def _check_company_account_control_ids(self):
        for journal in self.sudo():
            for account in journal.account_control_ids:
                if journal.company_id and account.company_id and \
                        journal.company_id != account.company_id:
                    raise ValidationError(
                        _('The Company in the Journal and in Accounts Allowed '
                          'must be the same.'))
        return True

    @api.multi
    @api.constrains('profit_account_id', 'company_id')
    def _check_company_profit_account_id(self):
        for journal in self.sudo():
            if journal.company_id and journal.profit_account_id.company_id and\
                    journal.company_id != journal.profit_account_id.company_id:
                raise ValidationError(_('The Company in the Journal and in '
                                        'Profit Account must be the same.'))
        return True

    @api.multi
    @api.constrains('loss_account_id', 'company_id')
    def _check_company_loss_account_id(self):
        for journal in self.sudo():
            if journal.company_id and journal.loss_account_id.company_id and\
                    journal.company_id != journal.loss_account_id.company_id:
                raise ValidationError(_('The Company in the Journal and in '
                                        'Loss Account must be the same.'))
        return True

    @api.constrains('company_id')
    def _check_company_id(self):
        for rec in self:
            move = self.env['account.move'].search(
                [('journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if move:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Move '
                      '%s.' % move.name))
            move_line = self.env['account.move.line'].search(
                [('journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if move_line:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Move Line '
                      '%s in Move %s.' % (move_line.name,
                                          move_line.move_id.name)))
            invoice = self.env['account.invoice'].search(
                [('journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if invoice:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Invoice '
                      '%s.' % invoice.name))
            bank_statement_line = self.env['account.bank.statement.line'].\
                search([('journal_id', '=', rec.id),
                        ('company_id', '!=', rec.company_id.id)], limit=1)
            if bank_statement_line:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Bank Statement Line '
                      '%s in Bank Statement %s.' % (
                        bank_statement_line.name,
                        bank_statement_line.statement_id.name)))
            bank_statement = self.env['account.bank.statement'].search(
                [('journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if bank_statement:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Bank Statement '
                      '%s.' % bank_statement.name))
            reconcile_model = self.env['account.reconcile.model'].search(
                [('journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if reconcile_model:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Reconcile Model '
                      '%s.' % reconcile_model.name))
            reconcile_model = self.env['account.reconcile.model'].search(
                [('second_journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if reconcile_model:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Reconcile Model '
                      '%s.' % reconcile_model.name))
            invoice_report = self.env['account.invoice.report'].search(
                [('journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if invoice_report:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Invoice Report '
                      '%s.' % invoice_report.name))
            common_report = self.env['account.common.report'].search(
                [('journal_ids', 'in', [rec.id]),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if common_report:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Report '
                      '%s.' % common_report.name))
            config_settings = self.env['account.config.settings'].search(
                [('currency_exchange_journal_id', '=', rec.id),
                 ('company_id', '!=', rec.company_id.id)], limit=1)
            if config_settings:
                raise ValidationError(
                    _('You cannot change the company, as this '
                      'Journal is assigned to Config Settings '
                      '%s.' % config_settings.name))

    def write(self, vals):
        for journal in self:
            if 'company_id' in vals:
                if journal.sequence_id.company_id.id != vals['company_id']:
                    journal.sequence_id.with_context(
                        bypass_company_validation=True).write(
                        {'company_id': vals['company_id']})
                elif journal.refund_sequence_id.company_id.id != vals[
                        'company_id']:
                    journal.refund_sequence_id.with_context(
                        bypass_company_validation=True).write(
                        {'company_id': vals['company_id']})
                if journal.default_debit_account_id.company_id.id != vals[
                        'company_id']:
                    journal.default_debit_account_id.with_context(
                        bypass_company_validation=True).write(
                        {'company_id': vals['company_id']})

                if journal.default_credit_account_id.company_id.id != vals[
                        'company_id']:
                    journal.default_credit_account_id.with_context(
                        bypass_company_validation=True).write(
                        {'company_id': vals['company_id']})

                if journal.bank_account_id.company_id.id != vals[
                        'company_id']:
                    company = self.env['res.company'].browse(
                        vals['company_id'])
                    journal.bank_account_id.with_context(
                        bypass_company_validation=True).write(
                        {'company_id': company.id,
                         'partner_id': company.partner_id.id})
        return super(AccountJournal, self).write(vals)
