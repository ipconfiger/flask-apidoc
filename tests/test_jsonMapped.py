# coding=utf8
import json
from unittest import TestCase


class TestJsonMapped(TestCase):
    def test_from_json_dict (self):
        from flask_doc.describer import JsonMapped, JsonProperty, JsonArrayProperty, StrLenBetween

        class OrderDetail(JsonMapped):
            item_sn = JsonProperty(unicode, required=True, help=u"item的SN", validators=[StrLenBetween(3, 5)])
            item_count = JsonProperty(int, help=u"item数量")

        class Order(JsonMapped):
            sn = JsonProperty(str, required=True, help=u"订单SN")
            fee = JsonProperty(float, required=True, help=u"订单金额")
            detail = JsonArrayProperty(OrderDetail, required=True)

        json_dt = dict(sn="asdasd", fee=12.09, detail=[dict(item_sn='abcd', item_count=5),])
        order = Order.from_json_dict(json_dt)
        self.assertEqual(order.sn, 'asdasd')
        self.assertEqual(order.fee, 12.09)
        self.assertEqual(order.detail[0].item_sn, "abcd")
        self.assertEqual(order.detail[0].item_count, 5)

