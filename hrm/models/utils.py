from odoo import models
from . import constraint


class Utils(models.Model):
    _name = 'hrm.utils'

    def default_block_(self):
        # Đặt giá trị mặc định cho Khối -> Khối thương mại
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_COMMERCE_NAME)]).id
        return ids

    def get_child_id(self, _object, table_name, parent):
        """
            Truy vấn tất cả các các phần tử là con
            _object là danh sách đối tượng cần truy vấn
            table_name là tên bảng
            parent là tên cột cha
        """
        list_object = []
        for ob in _object:
            query = f"""
                WITH RECURSIVE subordinates AS (
                SELECT id, {parent}
                FROM {table_name}
                WHERE id = {ob.id}
                UNION ALL
                SELECT t.id, t.{parent}
                FROM {table_name} t
                INNER JOIN subordinates s ON t.{parent} = s.id
            )
            SELECT id FROM subordinates;
            """
            self._cr.execute(query)
            temp = self._cr.fetchall()
            temp = [obj[0] for obj in temp]
            for t in temp:
                list_object.append(t)
        return list_object


