import math
from odoo import models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def massive_put_in_pack(self):
        move_lines = self

        if self.env.context.get('all_move_line_ids'):
            move_lines = self.env['stock.move.line'].browse(
                self.env.context['all_move_line_ids']
            )

        force_move_lines = bool(self.env.context.get('force_move_lines'))

        move_lines_to_pack, _packages_to_pack = (
            move_lines._get_lines_and_packages_to_pack(
                picked_first=not force_move_lines
            )
        )

        if not move_lines_to_pack:
            return False

        action = move_lines_to_pack._check_destinations()
        if action:
            return action

        for move_line in move_lines_to_pack:
            product_uom = move_line.product_id.uom_id
            line_uom = move_line.product_uom_id

            total_quantity = move_line.quantity_product_uom

            unit_count = math.floor(total_quantity)
            fraction_count = total_quantity - unit_count
            if unit_count <= 0:
                continue

            original_quantity = product_uom._compute_quantity(
                1.0,
                line_uom,
            )

            if unit_count > 1:
                move_line.write({
                    'quantity': original_quantity,
                })

            new_move_lines = self.env['stock.move.line']

            for _index in range(unit_count - 1):
                new_line = move_line.copy({
                    'quantity': 1.0,
                    'product_uom_id': product_uom.id,
                    'result_package_id': False,
                })
                new_move_lines |= new_line

            if fraction_count > 0:
                new_line = move_line.copy({
                    'quantity': fraction_count,
                    'product_uom_id': product_uom.id,
                    'result_package_id': False,
                })
                new_move_lines |= new_line

            for line in move_line | new_move_lines:
                line._put_in_pack()

        return True