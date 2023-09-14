BLOCK_OFFICE_NAME = "Văn phòng"
BLOCK_COMMERCE_NAME = "Thương mại"

DEFAULT_OFFICE = {
    'name': 'Văn phòng',
    'description': 'Khối văn phòng',
    'active': '1',
    'has_change': False,
    'create_new': True
}

DEFAULT_TRADE = {
    'name': 'Thương mại',
    'description': 'Khối thương mại',
    'active': '1',
    'has_change': False,
    'create_new': True
}

DO_NOT_DELETE = "Không thể xoá bản ghi này!"

DO_NOT_ARCHIVE = "Không thể lưu trữ bản ghi này!"

DUPLICATE_RECORD = 'Có bản ghi trùng lặp : %s'

SELECT_TYPE_COMPANY = [
    ('sale', 'Sale'),
    ('upsale', 'Upsale')]

PROFILE_STATUS = [
    ('incomplete', 'Chưa hoàn thiện'),
    ('complete', 'Hoàn thiện')]

TYPE_SYSTEM = [
    ('sale', 'Sale'),
    ('resale', 'Resale')
]
