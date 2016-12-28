# coding=utf8

from operator import itemgetter
import traceback
import sys
from flask import Blueprint, Response
import os
from jinja2 import Environment, FileSystemLoader


apidoc_bp = Blueprint('api-doc', __name__, template_folder='', url_prefix='/api-doc')

INSTANCE = None

@apidoc_bp.route('')
def response_index():
    """
    输出html
    :return:
    :rtype:
    """
    if not INSTANCE:
        return "Not initialized properly"
    return INSTANCE.generate_html()

@apidoc_bp.route('/html')
def response_html():
    """
    输出html
    :return:
    :rtype:
    """
    if not INSTANCE:
        return "Not initialized properly"
    return INSTANCE.generate_html()

@apidoc_bp.route('/md')
def response_markdown():
    """
    输出html
    :return:
    :rtype:
    """
    if not INSTANCE:
        return "Not initialized properly"
    return INSTANCE.generate_markdown()


@apidoc_bp.route('/loading.gif')
def loading_gif():
    """
    返回loading.gif
    :return:
    :rtype:
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loading.gif')
    with open(path, 'rb') as f:
        gif = f.read()
    response = Response(gif, mimetype="image/jpeg")
    return response


class FunctionDocument(object):
    """
    接口类的文档对象
    """
    def __init__(self, doc_string, url, method, endpoint, prefix):
        self.prefix = prefix
        self.endpoint = endpoint
        self.doc_string = doc_string
        self.url = url
        self.method = method
        self.show_idx = 0
        self.name = ""
        self.form_params = []
        self.query_params = []
        self.url_params = {}
        self.normal_lines = []
        self.return_lines = []
        self.document_format(doc_string)
        self.uid = 0

    def __getitem__(self, item):
        return getattr(self, item)

    def anchor(self):
        """
        返回锚点
        :return:
        :rtype:
        """
        return u"<a name=\"api-%s\"></a>" % self.show_idx

    def link(self):
        return u"<a href=\"#api-%s\">%s</a>" % (self.show_idx, self.name)

    def document_format(self, doc_str):
        """
        格式化API的doc_string到markdown格式
        :param doc_str:
        :type doc_str:
        :return:
        :rtype:
        """
        command_flag = "#idx:"
        form_param_flag = "@@"
        query_string_flag = "&&"
        url_param_flag = ":param"
        url_param_type_flag = ":type"
        lines = doc_str.split('\n')
        rt_mode = False
        for line in lines:
            s = line.strip()
            if rt_mode:
                if s.startswith(':rtype'):
                    rt_mode = False
                    continue
                self.return_lines.append(line)
                continue
            if s.startswith(command_flag):
                # 获取排序索引
                self.show_idx = int(s[5:])
                continue
            if s.startswith(form_param_flag):
                self.form_params.append([p.strip() for p in s[2:].split('|')])
                continue
            if s.startswith(query_string_flag):
                self.query_params.append([p.strip() for p in s[2:].split('|')])
                continue
            if s.startswith(url_param_flag):
                name, value = s[6:].split(':')
                self.url_params[name.strip()] = [name.strip(), None, value.strip()]
                continue
            if s.startswith(url_param_type_flag):
                name, value = s[6:].split(':')
                if name in self.url_params:
                    arr = self.url_params[name.strip()]
                    arr[1] = value.strip()
                    self.url_params[name.strip()] = arr
                continue
            if s.startswith(":return:"):
                rt_mode = True
                continue
            self.normal_lines.append(s)
        self.name = [line.strip() for line in self.normal_lines if line.strip()][0]

    def return_value(self):
        """
        获取返回值
        :return:
        :rtype:
        """
        lines = []
        for rt_line in self.return_lines:
            lines.append(u"%s" % rt_line)
        return u"\n".join(lines)

    def gen_markdown(self):
        """
        生成markdown文件
        :return:
        :rtype:
        """
        lines = [u"### %s" % self.name, u" ", u"#### Overview"]
        for normal_line in self.normal_lines[1:]:
            lines.append(u"> %s" % normal_line)
        lines.append(u"")
        lines.append(u"#### URL")
        lines.append(u"> %s" % self.url)
        lines.append(u"")
        lines.append(u"#### HTTP Method")
        lines.append(u"> %s" % self.method)
        if self.url_params:
            lines.append(u" ")
            lines.append(u"#### URL Parameter")
            lines.append(u" ")
            lines.append(u"| Name | Type | Description |")
            lines.append(u"|:----- |:----| --------- |")
            for k, param in self.url_params.iteritems():
                lines.append(u"|%s|" % u"|".join([p if p else u' ' for p in param]))
        lines.append(u" ")
        if self.query_params:
            lines.append(u" ")
            lines.append(u"#### QueryString Parameter")
            lines.append(u" ")
            lines.append(u"| Name | Require | Type | Description |")
            lines.append(u"|:----- |:---- |:----| --------- |")
            for param in self.query_params:
                lines.append(u"|%s|" % u"|".join(param if param else []))
        if self.form_params:
            lines.append(u" ")
            lines.append(u"#### Form Parameter")
            lines.append(u" ")
            lines.append(u"| Name | Require | Type | Description |")
            lines.append(u"|:----- |:---- |:----| --------- |")
            for param in self.form_params:
                lines.append(u"|%s|" % u"|".join(param if param else []))
        lines.append(u" ")
        lines.append(u"#### Return Value")
        lines.append(u" ")
        for rt_line in self.return_lines:
            lines.append(u"%s" % rt_line)
        lines.append(u" ")
        mark_down = u"\n".join(lines)
        return mark_down


class Generator(object):
    """
    生成器
    """
    def __init__(self, flask_app, filters=None):
        """
        初始化对象, 注入flask的App
        :param flask_app: flask的app对象
        :type flask_app: App
        :param filters: 过滤列表, 只显示部分选定blueprints的文档
        :type filters: [str...]
        """
        self.app = flask_app
        self.filters = filters
        self.functions = []
        global INSTANCE
        INSTANCE = self

    def prepare(self):
        """
        生成文档数据
        :return:
        :rtype:
        """
        api_items = []
        funcs = []
        rules_arr = []
        if self.filters:
            for filter in self.filters:
                api_items += [(k, v, filter) for k, v in self.app.view_functions.iteritems() if k.startswith(filter)]
                rules_arr += [(rule.endpoint, rule) for rule in self.app.url_map.iter_rules() if
                              rule.endpoint.startswith(filter)]
        else:
            api_items += [(k, v, ".") for k, v in self.app.view_functions.iteritems()]
            rules_arr += [(rule.endpoint, rule) for rule in self.app.url_map.iter_rules()]
        rules = dict(rules_arr)

        for api_name, api_func, prefix in api_items:
            rule = rules.get(api_name)
            url = rule.rule
            method = [m for m in list(rule.methods) if m != 'OPTIONS']
            doc = api_func.func_doc
            if not doc:
                continue
            funcs.append(FunctionDocument(doc.decode('utf8'), url, method, rule.endpoint, prefix))
        self.functions = sorted(funcs, key=itemgetter('prefix', 'show_idx'))
        for idx, f in enumerate(self.functions):
            f.uid = "api-%s" % idx


        for s_idx, fc in enumerate(self.functions):
            if fc.show_idx<1:
                fc.show_idx = s_idx
        self.app.register_blueprint(apidoc_bp)

    def generate_markdown(self):
        """
        生成markdown
        :return:
        :rtype:
        """
        doc_lines = [u"API Document", u"----------------", u" "]
        doc_lines.append(u"<center>")
        doc_lines.append(u"### TOC Index")
        doc_lines.append(u"</center>")
        doc_lines.append(u" ")
        doc_lines.append(u"| id | title |")
        doc_lines.append(u"|:----- |:--------- |")
        for doc_idx, doc in enumerate(self.functions):
            doc_lines.append(u"|%s|" % u"|".join([str(doc_idx), doc.link()]))
        doc_lines.append(u" ")
        doc_lines.append(u"---")

        for doc_idx, doc in enumerate(self.functions):
            doc_lines.append(doc.anchor())
            doc_lines.append(doc.gen_markdown())
            doc_lines.append(u" ")
            doc_lines.append(u"---")
        markdown = "\n".join([line.encode('utf8') for line in doc_lines])
        return markdown

    def generate_html(self):
        """
        生成html
        :return:
        :rtype:
        """
        path = os.path.dirname(os.path.abspath(__file__))
        template_env = Environment(
            autoescape=False,
            loader=FileSystemLoader(path),
            trim_blocks=False)

        return template_env.get_template('gen_template.html').render(gen=self)


def main():
    sys.path.append(os.getcwd())
    if len(sys.argv) < 2:
        print "Missing argument: mod_name:<Flask App> for Example manager:app"
        sys.exit(1)
    if len(sys.argv) > 2:
        filter_arr = sys.argv[2].split(',')
    else:
        filter_arr = None
    import_str = sys.argv[1]
    try:
        mod_name, var_name = import_str.split(":")
        mod = __import__(mod_name, globals(), locals(), fromlist=[var_name, ])
        app = getattr(mod, var_name)
        g = Generator(app, filters=filter_arr)
        g.prepare()
        print g.generate_markdown()
        sys.exit(0)
    except Exception as e:
        traceback.print_exc()
        print "Can not import Flask app from argument", import_str
        sys.exit(1)
