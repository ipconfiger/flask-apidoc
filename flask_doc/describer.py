# coding=utf8
import json
from functools import wraps

import logging

import datetime
from flask import request
from utils import func_sign, format_type

api_forms = {}
api_args = {}
api_json = {}

form_data = {}
args_data = {}

class BaseValidator(object):
    """
    基础验证器
    """
    validator = None
    help = None
    def setup(self, validator, helper_string):
        self.validator = validator
        self.help = helper_string

    def __repr__(self):
        return self.help


class StrLenBetween(BaseValidator):
    """
    验证字符串长度
    """
    def __init__(self, min_length, max_length):
        def validator(key, value):
            if value:
                assert isinstance(value, str) or isinstance(value, unicode), u"%s必须是字符串类型, 现在是%s" % (key, type(value))
                assert min_length <= len(value) <= max_length, u"%s的长度必须在%s和%s之间" % (key, min_length, max_length)
        self.setup(validator, u"字符串长度在%s到%s之间" % (min_length, max_length))


class NumberBetween(BaseValidator):
    """
    验证数字范围
    """
    def __init__(self, min_number, max_number):
        def validator(key, value):
            if value:
                assert value.isdigit() or _is_float(value), u"%s必须是数字类型(int或者float)"
                if value.isdigit():
                    assert min_number <= int(value) <= max_number, u"%s的值必须在%s和%s之间" % (key, min_number, max_number)
                if _is_float(value):
                    assert min_number <= float(value) <= max_number, u"%s的值必须在%s和%s之间" % (key, min_number, max_number)
        self.setup(validator, u"值的范围在%s到%s之间" % (min_number, max_number))


class ValidDateTime(BaseValidator):
    """
    验证是合法的日期格式
    """
    def __init__ (self, date_format):
        def validator(key, value):
            if value:
                try:
                    datetime.datetime.strptime(value, date_format)
                except:
                    assert False, u"%s格式不符合[%s] %s" % (key, date_format, value)
        self.setup(validator, u"需符合日期格式[%s]" % date_format)


class ValidEmail(BaseValidator):
    """
    验证是合法的邮箱地址
    """
    def valid_word(self, _str):
        vw = u"qazxswedcvfrtgbnhyujmkiolp1234567890QAZXSWEDCVFRTGBNHYUJMKIOPL.-_~"
        for w in _str:
            if w not in vw:
                return False
        return True

    def __init__(self):
        def validator(key, value):
            if value:
                assert u"@" in value, u"%s需要合法的邮件地址,当前值%s" % (key, value)
                px, domain = value.split(u'@')
                assert self.valid_word(px) and self.valid_word(domain) and len(domain.split(u'.')) >= 2, u"%s需要合法的邮件地址,当前值%s" % (key, value)
        self.setup(validator, u"必须为合法邮件地址")


class ValidUrl(BaseValidator):
    """
    验证是合法的URL
    """
    def __init__(self):
        def validator(key, value):
            if value:
                assert value[:7] == u'http://' or value[:8] == u'https://', u"%s必须为合法URL,当前值%s" % (key, value)
                assert len(value.split(u'.')) >= 2, u"%s必须为合法URL,当前值%s" % (key, value)

        self.setup(validator, u"必须为合法的URL")


def _is_float(s):
    return sum([n.isdigit() for n in s.strip().split('.')]) == 2

def gathering_form(ins):
    """
    生成一个类的实例, 然后将form或者args的内容, 付给这个类实例的属性
    :param ins: 
    :type ins: 
    :return: 
    :rtype: 
    """
    for k, v in form_data.iteritems():
        if v:
            if hasattr(ins, k):
                setattr(ins, k, v)
        else:
            logging.error(u"%s is %s", k, v)
    return ins


def gathering_args(ins):
    """
    生成一个类的实例, 然后将form或者args的内容, 付给这个类实例的属性
    :param ins: 
    :type ins: 
    :return: 
    :rtype: 
    """
    for k, v in args_data.iteritems():
        if v:
            if hasattr(ins, k):
                setattr(ins, k, v)
        else:
            logging.error(u"%s is %s", k, v)
    return ins

def gathering_body(data_type):
    """
    通过request.data 获取post的json字典
    :param data_type: 
    :type data_type: 
    :return: 
    :rtype: 
    """
    return data_type.from_json_dict(request.get_json())


class FieldDescribe(object):
    filed_name = ''
    required = True
    data_type = None
    help = ''
    validators = None

    def __repr__(self):
        return u"%s-%s-%s-%s" % (self.filed_name, self.required, self.data_type, self.help)

    def get_arr(self):
        return [self.filed_name, str(self.required), str(self.data_type).split("'")[1], self.help]

    def validate(self, dict):
        value = dict.get(self.filed_name)
        if self.required:
            assert value, u"%s不能为空" % self.filed_name

        if value and self.validators:
            for basevalidator in self.validators:
                basevalidator.validator(self.filed_name, value)

        if self.data_type == type(0.0):
            if value:
                if value.isdigit():
                    return float(value)
                assert _is_float(value), u"%s应该为浮点型,当前值%s" % (self.filed_name, value)
                return float(value)
            else:
                return 0.0
        if self.data_type == type(0):
            if value:
                assert value.isdigit(), u"%s必须为数字,当前值%s" % (self.filed_name, value)
                return int(value)
            else:
                return 0
        return value
        

def regist_fields (f, field_name, required, data_type, help, validators, is_form=False):
    desc = FieldDescribe()
    desc.filed_name = field_name
    desc.required = required
    desc.data_type = data_type
    desc.help = help
    desc.validators = validators
    if validators:
        lines = [u'<ul>']
        for basevalidator in validators:
            lines.append(u"<li>%s</li>" % basevalidator.help)
        lines.append(u"</ul>")
        desc.help = u"%s<br/>%s" % (desc.help, u"\n".join(lines))
    
    f_name = func_sign(f)
    if is_form:
        if f_name in api_forms:
            api_forms[f_name].append(desc)
        else:
            api_forms[f_name] = [desc]
    else:
        if f_name in api_args:
            api_args[f_name].append(desc)
        else:
            api_args[f_name] = [desc]

    return desc

def forms(field_name, required, data_type, help='', validators=None):
    def decorator(f):
        desc = regist_fields(f, field_name, required, data_type, help, validators, is_form=True)
        @wraps(f)
        def d_function(*args, **kwargs):
            value = desc.validate(request.form)
            form_data[field_name] = value
            ret_value = f(*args, **kwargs)
            form_data.clear()
            return ret_value
        return d_function
    return decorator


def args(field_name, required, data_type, help='', validators=None):
    def decorator(f):
        desc = regist_fields(f, field_name, required, data_type, help, validators)
        @wraps(f)
        def d_function (*args, **kwargs):
            value = desc.validate(request.args)
            args_data[field_name] = value
            ret_value = f(*args, **kwargs)
            args_data.clear()
            return ret_value
        return d_function
    return decorator


def json_form(data_type):
    def decorator(f):
        assert issubclass(data_type, JsonMapped), u"只能设置JsonMapped的子类"
        f_name = func_sign(f)
        api_json[f_name] = data_type
        @wraps(f)
        def d_function (*args, **kwargs):
            ret_value = f(*args, **kwargs)
            return ret_value
        return d_function
    return decorator
        

class JsonProperty(object):
    def __init__(self, data_type, required=False, help=None, validators=None):
        self.date_type = data_type
        self.required = required
        self.help = help
        self.validators = validators
        self.field_name = ''
        self.value = None

    def gen_doc(self):
        """
        生成文档
        :param name: 
        :type name: 
        :return: 
        :rtype: 
        """
        if issubclass(self.date_type, JsonMapped):
            return self.date_type().gen_doc()
        else:
            val = u";".join([basevalidator.help for basevalidator in self.validators]) if self.validators else u"无"
            return u"[%s]%s:%s 约束(%s)" % (format_type(self.date_type), u"必填" if self.required else u"非必填", self.help, val)

    def set_field(self, name, dt):
        """
        填入数据
        :param name: 
        :type name: 
        :param dt: 
        :type dt: 
        :return: 
        :rtype: 
        """
        self.field_name = name
        value = dt.get(self.field_name)
        if self.required:
            assert value != None, u"field:%s缺失-%s" % (name, value)
        if self.required and value:
            if self.date_type == str:
                assert type(value) == str or type(value) == unicode, u"field:%s类型不为%s,实际为%s" % (name, self.date_type, type(value))
            if self.date_type == float:
                assert type(value) == float or type(value) == int, u"field:%s类型不为%s,实际为%s" % (name, self.date_type, type(value))
            if self.date_type == int:
                assert type(value) == int, u"field:%s类型不为%s,实际为%s" % (name, self.date_type, type(value))
            if self.validators:
                if value != None:
                    for validator in self.validators:
                        validator.validator(name, unicode(value))

        if issubclass(self.date_type, JsonMapped):
            if self.required:
                assert type(value) == dict, u"field:%s类型不正确:%s" % (name, type(value))
            if value != None:
                self.value = self.date_type.from_json_dict(value)
                return
            else:
                self.value = None
                return
        self.value = value

    def clear(self):
        pass


class JsonArrayProperty(object):
    def __init__(self, data_type, required=False, help=None):
        self.data_type = data_type
        self.required = required
        self.help = help
        self.value = []

    def gen_doc(self):
        """
        生成文档
        :param name: 
        :type name: 
        :return: 
        :rtype: 
        """
        doc_root = []
        if issubclass(self.data_type, JsonMapped):
            doc_root.append(self.data_type().gen_doc())
            return doc_root
        else:
            return u"[%s,]" % self.data_type


    def set_field(self, name, dt):
        """
        设值
        :param name: 
        :type name: 
        :param dt: 
        :type dt: 
        :return: 
        :rtype: 
        """
        self.field_name = name
        value = dt.get(name)
        if self.required:
            assert value, u"field:%s缺失-%s" % (name, value)
        if value:
            assert type(value) == type([]), u"field:%s类型不为数组:%s" % (name, type(value))
            for item in value:
                if type(item) == dict:
                    assert issubclass(self.data_type, JsonMapped), u"field:%s数组内数据格式不正确:%s" % (name, value)
                    v = self.data_type.from_json_dict(item)
                    self.value.append(v)
                else:
                    assert type(item) == self.data_type, u"field:%s数组内数据类型与定义不符-定义:%s 实际%s" % (name, self.data_type, type(item))
                    self.value.append(item)

    def clear(self):
        self.value = []


class JsonMapped(object):
    """
    作为json解析的基类, 实现对复杂对象的JSON处理器
    """
    private_json_dict = None
    def gen_doc(self):
        """
        生成文档
        :return: 
        :rtype: 
        """
        doc_root = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if not (isinstance(attr, JsonProperty) or isinstance(attr, JsonArrayProperty)):
                continue
            doc_root[attr_name] = attr.gen_doc()
        return doc_root

    def as_json(self):
        return json.dumps(self.private_json_dict, indent=2, ensure_ascii=False)

    @classmethod
    def from_json_dict(cls, dt):
        ins = cls()
        ins.private_json_dict = dt
        for attr_name in dir(ins):
            attr = getattr(ins, attr_name)
            if not (isinstance(attr, JsonProperty) or isinstance(attr, JsonArrayProperty)):
                continue
            attr.set_field(attr_name, dt)
            setattr(ins, attr_name, attr.value)
            attr.clear()
        return ins


class ResponseViewBase(object):
    """
    定义返回值结构, 并生成返回的JSON
    """
    pass
