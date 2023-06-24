from datetime import datetime

from apps.app import db


# 拾得物基本クラス
# UIの左上から右下方向の順番
class LostItem(db.Model):
    __tablename__ = "lost_item"
    id = db.Column(db.Integer, primary_key=True)
    choice_finder = db.Column(db.String)
    track_num = db.Column(db.Integer)
    notify = db.Column(db.Boolean, default=False)
    # 拾得日時
    get_item = db.Column(db.DateTime, default=datetime.now)
    get_item_hour = db.Column(db.String)
    get_item_minute = db.Column(db.String)
    # 受付日時
    recep_item = db.Column(db.DateTime, default=datetime.now)
    recep_item_hour = db.Column(db.String)
    recep_item_minute = db.Column(db.String)
    recep_manager = db.Column(db.String)

    # 拾得者情報等の管理
    find_area = db.Column(db.String)
    find_area_police = db.Column(db.String)
    own_waiver = db.Column(db.String)
    finder_name = db.Column(db.String)
    own_name_note = db.Column(db.String)
    finder_age = db.Column(db.Integer)
    finder_sex = db.Column(db.String)
    finder_post = db.Column(db.String)
    finder_tel1 = db.Column(db.String)
    finder_tel2 = db.Column(db.String)

    # 拾得物の詳細情報
    item_class_L = db.Column(db.String)
    item_class_M = db.Column(db.String)
    item_class_S = db.Column(db.String)
    item_value = db.Column(db.Boolean, default=False)
    item_feature = db.Column(db.String)
    item_color = db.Column(db.String)
    item_storage = db.Column(db.String, default="アリオ亀有")
    item_storage_place = db.Column(db.String)
    item_maker = db.Column(db.String)
    item_expiration = db.Column(db.DateTime)
    item_num = db.Column(db.Integer)
    item_unit = db.Column(db.String)
    item_plice = db.Column(db.String)
    item_money = db.Column(db.String)
    item_remarks = db.Column(db.String)
    item_situation = db.Column(db.Boolean, default=False)
    item_image = db.Column(db.String)

    # 占有者用入力項目
    finder_class = db.Column(db.String)
    finder_affiliation = db.Column(db.String)

    # 第三者用入力項目
    thirdparty_waiver = db.Column(db.String)
    thirdparty_name_note = db.Column(db.String)

    def to_dict(self):
        return {
            'id': self.id,
            'choice_finder': self.choice_finder,
            'track_num': self.track_num,
            'notify': self.notify,
            'get_item': self.get_item,
            'get_item_hour': self.get_item_hour,
            'get_item_minute': self.get_item_minute,
            'recep_item': self.recep_item,
            'recep_item_hour': self.recep_item_hour,
            'recep_item_minute': self.recep_item_minute,
            'recep_manager': self.recep_manager,
            'find_area': self.find_area,
            'find_area_police': self.find_area_police,
            'own_waiver': self.own_waiver,
            'finder_name': self.finder_name,
            'own_name_note': self.own_name_note,
            'finder_age': self.finder_age,
            'finder_sex': self.finder_sex,
            'finder_post': self.finder_post,
            'finder_tel1': self.finder_tel1,
            'finder_tel2': self.finder_tel2,
            'item_class_L': self.item_class_L,
            'item_class_M': self.item_class_M,
            'item_class_S': self.item_class_S,
            'item_value': self.item_value,
            'item_feature': self.item_feature,
            'item_color': self.item_color,
            'item_storage': self.item_storage,
            'item_storage_place': self.item_storage_place,
            'item_maker': self.item_maker,
            'item_expiration': self.item_expiration,
            'item_num': self.item_num,
            'item_unit': self.item_unit,
            'item_plice': self.item_plice,
            'item_money': self.item_money,
            'item_remarks': self.item_remarks,
            'item_situation': self.item_situation,
            'item_image': self.item_image,
            'finder_class': self.finder_class,
            'finder_affiliation': self.finder_affiliation,
            'thirdparty_waiver': self.thirdparty_waiver,
            'thirdparty_name_note': self.thirdparty_name_note
        }
