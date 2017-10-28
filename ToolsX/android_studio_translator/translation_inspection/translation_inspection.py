import re

from android_studio_translator.delete_action import DeleteAction
from android_studio_translator.tools import Tools
from xx import filex
from xx import iox


class TranslationInspection:
    """
    有一个问题，就是判断''被错误翻译成""的时候，没有判断引号中的内容是否一致
    """

    def main(self):
        pseudo_file = 'data/project_save.tmx'
        translation_file = 'data/project_save.tmx'
        inspection_list = [
            StandardTranslation.inspect_translation,
            TranslationInspection.inspect_double_quote,
            TranslationInspection.inspect_single_quote,
            TranslationInspection.inspect_double_single_quote,
            TranslationInspection.inspect_parentheses,
            TranslationInspection.inspect_ends_symbol,
            TranslationInspection.inspect_short_cut,
            TranslationInspection.inspect_space,
        ]
        action_list = [
            ['退出', exit],
            ['检查', self.inspect_file, translation_file, translation_file, inspection_list, None, False, False],
        ]
        iox.choose_action(action_list)

    @staticmethod
    def inspect_file(pseudo_file, translation_file, inspection_list, result_file=None, print_msg=False,
                     print_change=False):
        """
        
        :param pseudo_file: 伪翻译文件，也可以与翻译文件相同，用于自校检
        :param translation_file: 翻译文件
        :param inspection_list: 要检测的方法列表，如检测tips时是不需要检测快捷方式的
        :param result_file: 结果文件
        :param print_msg: 是否输出操作时的消息
        :param print_change: 是否输出更改时的消息，如果2个都置为False，可以查看需要处理的内容
        :return: 
        """
        if result_file is None:
            result_file = filex.get_result_file_name(translation_file, '_inspection')
        pseudo_dict = Tools.get_dict_from_omegat(pseudo_file)
        translation_dict = Tools.get_dict_from_omegat(translation_file)
        print('pseudo size is %d' % (len(pseudo_dict)))
        print('translation size is %d' % (len(translation_dict)))
        result = dict()
        i = 0
        for en in pseudo_dict.keys():
            cn_key = None
            if en in translation_dict.keys():
                cn_key = en
            else:
                abbreviated_en = DeleteAction.delete_all_symbol_of_string(en, False)
                if abbreviated_en in translation_dict.keys():
                    cn_key = abbreviated_en
            if cn_key:
                value = translation_dict[cn_key]
                if not value:
                    continue
                translation_dict.pop(cn_key)
                old = value
                for inspection in inspection_list:
                    value = inspection(en, value, print_msg)
                if old != value:
                    if print_change:
                        i += 1
                        print('\n%d.【%s】根据【%s】被修改为\n【%s】\n' % (i, old, en, value))
                result[en] = value
            else:
                print('不包含key:%s' % en)
        print('remain translation size %d' % (len(translation_dict)))
        Tools.save_omegat_dict(result, result_file)

    @staticmethod
    def inspect(en, cn):
        """提取出方法方便外部调用"""
        inspection_list = [
            StandardTranslation.inspect_translation,
            TranslationInspection.inspect_double_quote,
            TranslationInspection.inspect_single_quote,
            TranslationInspection.inspect_double_single_quote,
            TranslationInspection.inspect_parentheses,
            TranslationInspection.inspect_ends_symbol,
            TranslationInspection.inspect_short_cut,
            TranslationInspection.inspect_space,
        ]
        for inspection in inspection_list:
            cn = inspection(en, cn, False)
        return cn

    @staticmethod
    def inspect_space(en, cn, print_msg=False):
        """
        检查汉字与英文（或{\d}）之间是否添加了空格
        """
        chinese_pattern = r'([\u4e00-\u9fa5])'
        # 字母，或{0}，或''{0}''
        # need_space_pattern = r'([a-zA-Z]|{\d}+|\'\'{\d}\'\')'

        # 测试发现有一些没有完全替换，使用 .+? 也不会过多替换
        # need_space_pattern = r'([a-zA-Z]|{\d}+|\'\'.+?\'\')'

        # 再进一步，即使单个引号也不会有错误的
        need_space_pattern = r'([a-zA-Z]|{\d}+|\'.+?\')'
        double_quote_pattern = r'\''

        cn = re.sub(chinese_pattern + need_space_pattern, r'\1 \2', cn)
        cn = re.sub(need_space_pattern + chinese_pattern, r'\1 \2', cn)

        all_match = re.findall(r'\'\s(.+?)\s\'', cn)
        if all_match:
            for match in all_match:
                match_without_quote_space = '\' %s \'' % match
                match_without_quote = '\'%s\'' % match
                if match_without_quote in en:
                    if print_msg:
                        print('翻译的双引号中有空格，而原文没有，将其空格删除【%s】' % match_without_quote_space)
                    cn = cn.replace(match_without_quote_space, match_without_quote)

        if re.search(chinese_pattern + double_quote_pattern, cn):
            print('【%s】在中文后有相连的引号' % cn)
        if re.search(double_quote_pattern + chinese_pattern, cn):
            print('【%s】在中文前有相连的引号' % cn)
        return cn

    @staticmethod
    def inspect_short_cut(en, cn, print_msg=False):
        """
        检查快捷键
        处理&形式快捷方式
        下划线的快捷方式经常会有问题，一定要注意处理
        """
        cn = TranslationInspection.search_and_replace(en, cn, r'(?<!\\)&(\w)', r'(&%s)',
                                                      print_msg=print_msg)
        return cn

    @staticmethod
    def search_and_replace(en, cn, pattern, replace, group=1, print_msg=False):
        match = re.search(pattern, en)
        if match is not None:
            content = match.group(group)
            if print_msg:
                print('\n【%s】匹配，翻译是【%s】,内容是【%s】' % (en, cn, content))
            append = replace % content
            if not cn.endswith(append):
                ignore_list = [
                    'shortcut:',
                    'productName;',
                ]
                contain_ignore = False
                for ignore_word in ignore_list:
                    if '&%s' % ignore_word in cn:
                        contain_ignore = True
                        break
                if not contain_ignore:
                    print('【%s】not endswith 【%s】' % (cn, append))
                    cn += append
        return cn

    @staticmethod
    def inspect_ends_symbol(en, cn, print_msg=False):
        """
        检查结尾的符号
        """
        pattern = r'(\s?([.。…\\:：])+)$'
        en_match = re.search(pattern, en)
        if en_match:
            if print_msg:
                print('\n【%s】包含结尾符号，翻译是【%s】' % (en, cn))
            en_content = en_match.group(1)
            if en_content == '.':
                # 将句点替换为句号
                en_content = '。'
            if not re.search(pattern, cn):
                # 忽略已经有的快捷方式
                if not re.search(pattern, re.sub(r'\([_&]\w\)', '', cn)):
                    # 这里要添加的时候把快捷方式删了
                    match = re.search(r'(\([_&]\w\))', cn)
                    if match is not None:
                        cn = re.sub(r'\(([_&]\w\))', '', cn) + en_content + match.group(1)
                    else:
                        cn = cn + en_content
                    if print_msg:
                        print('在结尾添加%s' % en_content)
        return cn

    @staticmethod
    def inspect_parentheses(en, cn, print_msg=False):
        """
        检查()不翻译为（），同时如果是方法后的()后面加上空格
        """
        pattern = r'\(.*?\)'
        en_match_list = re.findall(pattern, en)
        if en_match_list:
            if print_msg:
                print('\n【%s】包含小括号，翻译是【%s】' % (en, cn))
            if len(en_match_list) == cn.count('（') and len(en_match_list) == cn.count('）'):
                if print_msg:
                    print('被翻译成了【（）】,替换')
                cn = cn.replace('（', '(')
                cn = cn.replace('）', ')')

            chinese_pattern = r'([\u4e00-\u9fa5])'
            need_space_pattern = r'(\(\))'
            old = cn
            cn = re.sub(need_space_pattern + chinese_pattern, r'\1 \2', cn)
            if old != cn:
                if print_msg:
                    print('补充括号后的空格')
        return cn

    @staticmethod
    def inspect_double_single_quote(en, cn, print_msg=False):
        """
        检查''(2个')也按原来的保持''，去除中间的空格，同时前后如果是字母加上空格
        """
        # 因为会有don''t之类的，过滤t
        pattern = r'\'{2}(.+?)\'{2}(?!t)'
        en_match_list = re.findall(pattern, en)
        if en_match_list:
            if print_msg:
                print('\n【%s】包含两个单引号，翻译是【%s】' % (en, cn))
            if len(en_match_list) == cn.count('“') and len(en_match_list) == cn.count('”'):
                if print_msg:
                    print('被翻译成了【“”】,替换')
                cn = cn.replace('“', '\'\'')
                cn = cn.replace('”', '\'\'')
            if len(en_match_list) * 2 == cn.count('"') and '="' not in cn:
                if print_msg:
                    print('被翻译成了【"】，替换')
                cn = cn.replace('"', "\'\'")
            old = cn
            cn = re.sub(r'\s*(\')\s*', r'\1', cn)
            if old != cn:
                if print_msg:
                    print('去除单引号前后的空格')
            cn_match_list = re.findall(pattern, cn)
            if not cn_match_list:
                for en_match in en_match_list:
                    all_quote = '\'\'' + en_match + '\'\''
                    if en_match in cn and all_quote not in cn:
                        left_quote = '\'\'' + en_match + '\''
                        right_quote = '\'' + en_match + '\'\''
                        if left_quote in cn:
                            if print_msg:
                                print('右边缺\'，添加')
                            cn = cn.replace(left_quote, all_quote)
                        elif right_quote in cn:
                            if print_msg:
                                print('左边缺\'，添加')
                            cn = cn.replace(right_quote, all_quote)
                        else:
                            if print_msg:
                                print('左右缺\'\'，添加')
                            cn = cn.replace(en_match, all_quote)
            cn_match_list = re.findall(pattern, cn)
            if not cn_match_list:
                print('中文中没有结果')
                print('\n【%s】包两个单引号，翻译是【%s】,内容是【%s】' % (en, cn, ''))
                return cn
            if len(en_match_list) != len(cn_match_list):
                print('匹配结果的大小不相等')
                print('\n【%s】包两个单引号，翻译是【%s】,内容是【%s】' % (en, cn, ''))
                return cn
            # 如果前后跟字母，则补充空格
            old = cn
            cn = re.sub(r'([a-zA-Z]+)(\'\')', r'\1 \2', cn)
            cn = re.sub(r'(\'\')([a-zA-Z]+)', r'\1 \2', cn)
            if old != cn:
                if print_msg:
                    print('补充与字母相联的''的空格')
        return cn

    @staticmethod
    def inspect_single_quote(en, cn, print_msg=False):
        """检查单引号"""
        # 只有一个单引号，前后不能有，不知如何表示更好，就写成了这样
        pattern = r'(?<!\')\'(?!\')(.+?)(?<!\')\'(?!\')'
        en_match_list = re.findall(pattern, en)
        if en_match_list:
            if print_msg:
                print('\n【%s】包含成对单引号，翻译是【%s】' % (en, cn))

            cn_match_list = re.findall(pattern, cn)
            if len(en_match_list) != len(cn_match_list):
                if len(en_match_list) == cn.count('“') and len(en_match_list) == cn.count('”'):
                    if print_msg:
                        print('被翻译成了【“”】,替换')
                    cn = cn.replace('“', '\'')
                    cn = cn.replace('”', '\'')
                elif len(en_match_list) == cn.count('‘') and len(en_match_list) == cn.count('’'):
                    if print_msg:
                        print('被翻译成了【‘’】,替换')
                    cn = cn.replace('‘', '\'')
                    cn = cn.replace('’', '\'')
                elif len(en_match_list) * 2 == cn.count('"'):
                    if print_msg:
                        print('被翻译成了【"】,替换')
                    cn = cn.replace('"', '\'')

            cn_match_list = re.findall(pattern, cn)
            if len(en_match_list) != len(cn_match_list):
                print('\n【%s】包含成对单引号，翻译是【%s】' % (en, cn))
                print('匹配结果的大小不相等')
                print(en_match_list)
                print(cn_match_list)
                return cn
            for i in range(len(en_match_list)):
                en_content = en_match_list[i]
                cn_content = cn_match_list[i]
                if en_content != cn_content and en_content == cn_content.strip():
                    if print_msg:
                        print('翻译中引号中的内容带有空格，删除')
                    cn = cn.replace('\'' + cn_content + '\'', '\'' + cn_content.strip() + '\'')
                    cn_content_with_quotation = cn_content.strip()
                else:
                    cn_content_with_quotation = cn_content
                cn_content_with_quotation = '\'' + cn_content_with_quotation + '\''
                if not cn.startswith(cn_content_with_quotation) and ' ' + cn_content_with_quotation not in cn:
                    cn = cn.replace(cn_content_with_quotation, ' ' + cn_content_with_quotation)
                if not cn.endswith(cn_content_with_quotation) and cn_content_with_quotation + ' ' not in cn:
                    cn = cn.replace(cn_content_with_quotation, cn_content_with_quotation + ' ')
        return cn

    @staticmethod
    def inspect_double_quote(en, cn, print_msg=False):
        """
        检查""，不使用“”，删去中间的空格
        """
        pattern = r'"(.+?)"'
        en_match = re.search(pattern, en)
        if en_match is not None:
            en_content = en_match.group(1)
            if print_msg:
                print('【%s】包含双引号，翻译是【%s】,内容是【%s】' % (en, cn, en_content))
            if en.count('"') == 2 and cn.count('“') == 1 and cn.count('”') == 1:
                if print_msg:
                    print('【""】被翻译成了【“”】，替换')
                cn = cn.replace('“', '\"')
                cn = cn.replace('”', '\"')
            cn_match = re.search(pattern, cn)
            if cn_match is not None:
                cn_content = cn_match.group(1)
                if en_content != cn_content and en_content == cn_content.strip():
                    if print_msg:
                        print('翻译中引号中的内容带有空格，删除')
                    cn = re.sub(pattern, '"%s"' % (cn_content.strip()), cn)
        return cn


class StandardTranslation:
    """
    标准的翻译，可用,分隔
    英文|中文|不使用|备注
    """

    standard_translation_file = r'D:\workspace\BlogX\Chinglish\AndroidStudio\[2375]AndroidStudio汉化中使用的统一翻译.txt'
    standard_translation = list()

    def __init__(self, en, cn, replace):
        self.en_list = en.split(',')
        self.cn_list = cn.split(',')
        if replace:
            self.replace_list = replace.split(',')
        else:
            self.replace_list = []

    @staticmethod
    def get_standard_translation():
        """
        获取标准翻译
        """
        result = list()
        with open(StandardTranslation.standard_translation_file, encoding='utf-8') as file:
            all_lines = file.readlines()
            for line in all_lines:
                # 取小写
                line = line.rstrip('\n').lower()
                if '|' in line:
                    split_result = line.split('|')
                    en = split_result[0]
                    if len(split_result) > 1:
                        cn = split_result[1]
                    else:
                        cn = en
                    if len(split_result) > 2:
                        replace = split_result[2]
                    else:
                        replace = None
                    if en != '-':
                        result.append(StandardTranslation(en, cn, replace))
        return result

    @staticmethod
    def inspect_translation(en, cn, print_msg=False):
        """
        检查翻译是否准确，是否使用统一的翻译
        """
        en = en.lower()
        if not StandardTranslation.standard_translation:
            StandardTranslation.standard_translation = StandardTranslation.get_standard_translation()
        for standard_translation in StandardTranslation.standard_translation:
            for s_en in standard_translation.en_list:
                # 可能含标点符号，用空格分不准确
                if s_en in en.split(' '):
                    contain = False
                    for s_cn in standard_translation.cn_list:
                        if s_cn in cn:
                            contain = True
                            break
                    if not contain:
                        has_replace = False
                        if standard_translation.replace_list:
                            for replace in standard_translation.replace_list:
                                # 可能不只有一个
                                if cn.count(replace) == 1:
                                    # 只有一个，进行替换
                                    if print_msg:
                                        print('将【%s】替换为【%s】' % (replace, standard_translation.cn_list[0]))
                                    cn = cn.replace(replace, standard_translation.cn_list[0])
                                    has_replace = True
                        if not has_replace:
                            print('\n【%s】的翻译\n【%s】中不包含期望的翻译\n【%s】应该翻译为【%s】' % (
                                en, cn, s_en, ','.join(standard_translation.cn_list)))

        return cn


if __name__ == '__main__':
    TranslationInspection().main()
