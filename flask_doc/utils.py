# coding=utf8

def func_sign(func):
    """
    生成函数签名
    :param func: 
    :type func: 
    :return: 
    :rtype: 
    """
    return "%s.%s" % (func.__module__, func.func_name)
