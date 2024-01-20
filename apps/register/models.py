from datetime import datetime

from apps.app import db


# 拾得物基本クラス
# UIの左上から右下方向の順番
class LostItem(db.Model):
    __tablename__ = "lost_item"
    id = db.Column(db.Integer, primary_key=True)
    main_id = db.Column(db.Integer)
    current_year = db.Column(db.Integer)

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
    finder_address = db.Column(db.String)
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
    item_situation = db.Column(db.String)
    item_image = db.Column(db.String)
    item_bundled = db.relationship(
        "BundledItems", backref="bundled_item", cascade="all, delete-orphan"
    )
    item_denomination = db.relationship(
        "Denomination", backref="denomination_item", cascade="all, delete-orphan"
    )

    # 占有者用入力項目
    finder_class = db.Column(db.String)
    finder_affiliation = db.Column(db.String)

    # 第三者用入力項目
    thirdparty_waiver = db.Column(db.String)
    thirdparty_name_note = db.Column(db.String)

    # カードの場合の追加情報
    card_campany = db.Column(db.String)
    card_tel = db.Column(db.String)
    card_name = db.Column(db.String)
    card_person = db.Column(db.String)
    card_return = db.Column(db.DateTime)
    card_item = db.Column(db.DateTime)
    card_item_hour = db.Column(db.String)
    card_item_minute = db.Column(db.String)
    card_manager = db.Column(db.String)

    # 遺失者連絡
    lost_date = db.Column(db.DateTime)
    lost_hour = db.Column(db.String)
    lost_minute = db.Column(db.String)
    lost_area = db.Column(db.String)
    lost_person = db.Column(db.String)
    lost_class = db.Column(db.String)
    lost_affiliation = db.Column(db.String)
    lost_tel1 = db.Column(db.String)
    lost_tel2 = db.Column(db.String)
    lost_post = db.Column(db.String)
    lost_address = db.Column(db.String)
    note_date = db.Column(db.DateTime)
    note_hour = db.Column(db.String)
    note_minute = db.Column(db.String)
    note_process = db.Column(db.String)
    note_manager = db.Column(db.String)
    response_date = db.Column(db.DateTime)
    response_hour = db.Column(db.String)
    response_minute = db.Column(db.String)
    response_expect = db.Column(db.DateTime)
    response_content = db.Column(db.String)
    response_remarks = db.Column(db.String)

    # 返還
    return_date = db.Column(db.DateTime)
    return_check = db.Column(db.String)
    return_person = db.Column(db.String)
    return_address = db.Column(db.String)
    return_tel = db.Column(db.String)
    return_manager = db.Column(db.String)

    # 還付処理等
    police_date = db.Column(db.DateTime)
    receiptnumber = db.Column(db.Integer)
    refund_expect = db.Column(db.DateTime)
    refund_date = db.Column(db.DateTime)
    refund_situation = db.Column(db.String)
    refund_manager = db.Column(db.String)
    refunded_process = db.Column(db.String)
    refunded_process_manager = db.Column(db.String)
    refunded_process_sub_manager = db.Column(db.String)
    refunded_date = db.Column(db.DateTime)

    # 廃棄処理
    disposal_date = db.Column(db.DateTime)
    selling_price = db.Column(db.Integer)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# 同梱物クラス
class BundledItems(db.Model):
    __tablename__ = "bundled_item"
    # 基本情報
    id = db.Column(db.Integer, primary_key=True)
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
    item_situation = db.Column(db.String)
    lostitem_id = db.Column(db.Integer, db.ForeignKey("lost_item.id"))

    # カードの場合の追加情報
    card_campany = db.Column(db.String)
    card_tel = db.Column(db.String)
    card_name = db.Column(db.String)
    card_person = db.Column(db.String)
    card_return = db.Column(db.DateTime)
    card_item = db.Column(db.DateTime)
    card_item_hour = db.Column(db.String)
    card_item_minute = db.Column(db.String)
    card_manager = db.Column(db.String)


# 金種クラス
class Denomination(db.Model):
    __tablename__ = "denomination"
    # 金種情報
    id = db.Column(db.Integer, primary_key=True)
    ten_thousand_yen = db.Column(db.Integer)
    five_thousand_yen = db.Column(db.Integer)
    two_thousand_yen = db.Column(db.Integer)
    one_thousand_yen = db.Column(db.Integer)
    five_hundred_yen = db.Column(db.Integer)
    one_hundred_yen = db.Column(db.Integer)
    fifty_yen = db.Column(db.Integer)
    ten_yen = db.Column(db.Integer)
    five_yen = db.Column(db.Integer)
    one_yen = db.Column(db.Integer)
    total_yen = db.Column(db.Integer)
    item_situation = db.Column(db.String)

    # 記念硬貨
    commemorative_coin_1 = db.Column(db.String)
    commemorative_coin_1_value = db.Column(db.String)
    commemorative_coin_2 = db.Column(db.String)
    commemorative_coin_2_value = db.Column(db.String)
    lostitem_id = db.Column(db.Integer, db.ForeignKey("lost_item.id"))


# 遺失物クラス
class NotFound(db.Model):
    __tablename__ = "notfound"
    id = db.Column(db.Integer, primary_key=True)
    # 紛失日時
    lost_item = db.Column(db.DateTime, default=datetime.now)
    lost_item_hour = db.Column(db.String)
    lost_item_minute = db.Column(db.String)
    # 受付日時
    recep_item = db.Column(db.DateTime, default=datetime.now)
    recep_item_hour = db.Column(db.String)
    recep_item_minute = db.Column(db.String)
    recep_manager = db.Column(db.String)

    # 拾得者情報等の管理
    lost_area = db.Column(db.String)
    lost_name = db.Column(db.String)
    lost_age = db.Column(db.Integer)
    lost_sex = db.Column(db.String)
    lost_post = db.Column(db.String)
    lost_address = db.Column(db.String)
    lost_tel1 = db.Column(db.String)
    lost_tel2 = db.Column(db.String)

    # 拾得物の詳細情報
    item_class_L = db.Column(db.String)
    item_class_M = db.Column(db.String)
    item_class_S = db.Column(db.String)
    item_value = db.Column(db.Boolean, default=False)
    item_feature = db.Column(db.String)
    item_color = db.Column(db.String)
    item_maker = db.Column(db.String)
    item_expiration = db.Column(db.DateTime)
    item_num = db.Column(db.Integer)
    item_unit = db.Column(db.String)
    item_plice = db.Column(db.String)
    item_money = db.Column(db.String)
    item_remarks = db.Column(db.String)
    item_situation = db.Column(db.String)

    # カードの場合の追加情報
    card_campany = db.Column(db.String)
    card_tel = db.Column(db.String)
    card_name = db.Column(db.String)
    card_person = db.Column(db.String)
    card_return = db.Column(db.DateTime)
    card_item = db.Column(db.DateTime)
    card_item_hour = db.Column(db.String)
    card_item_minute = db.Column(db.String)
    card_manager = db.Column(db.String)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
