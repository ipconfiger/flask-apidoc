# coding=utf8

def js_string_to_html(_str):
    lines =[]
    for l in _str.split(u'\n'):
        line = l.replace(u' ', u"&nbsp;")
        lines.append(line)
    return u"<br/>".join(lines)

def format_type(str_type):
    """
    简化类型输出的格式
    :param str_type: 
    :type str_type: 
    :return: 
    :rtype: 
    """
    type_name = str(str_type)[7:-2]
    if type_name == "unicode":
        return "str"
    return type_name


def func_sign(func):
    """
    生成函数签名
    :param func: 
    :type func: 
    :return: 
    :rtype: 
    """
    return "%s.%s" % (func.__module__, func.func_name)
