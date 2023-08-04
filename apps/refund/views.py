from flask import Blueprint, render_template

refund = Blueprint(
    "refund",
    __name__,
    template_folder="templates",
    static_folder="static",
)


# 届出受理番号登録
@refund.route("/register_num", methods=["POST", "GET"])
def register_num():
    return render_template("refund/index.html")
