from xml.etree import ElementTree as Et
from xx import iox
from xx import filex
from xx import encodex
import re
from android_studio_translator import translation_tools as tool


class Tools:
    def main(self):
        # 1原文件
        en_file = 'bundle/ActionsBundle_en.properties'
        # 2汉化文件
        unicode_file = 'bundle/ActionsBundle_unicode.properties'
        # 3转为中文
        cn_file = 'bundle/ActionsBundle_cn.properties'
        # 4修改断句的文件
        cn_split_file = 'bundle/ActionsBundle_cn_split.properties'
        cn_modified_file = 'bundle/ActionsBundle_cn_modified.properties'
        # 英文修改过的文件，删除快捷方式，删除末尾的.或省略号
        en_modified_file = 'bundle/ActionsBundle_en_modified.properties'

        omega_tmx_file = 'bundle/project_save.tmx.xml'
        action_list = [
            ['退出', exit],
            ['参照翻译(未翻译保留)', self.translate_file_by_reference, en_file, cn_modified_file],
            ['参照翻译(未翻译标记)', self.translate_file_by_reference, en_file, cn_modified_file, None, '%s=%s【未翻译】'],
            ['将文件的unicode转为中文', self.change_unicode_to_chinese, unicode_file],
            ['将文件的中文转为unicode', self.change_chinese_to_unicode, cn_file],
            ['将中文翻译结果导出为OmegaT数据（可用于检查换行）', self.convert_to_omegat_dict, en_file, cn_modified_file, omega_tmx_file],
            ['处理ActionsBundle_en.properties', self.process_file_for_translation, en_file],
            ['处理ActionsBundle_cn_split.properties', self.process_file_for_translation, cn_split_file,
             cn_modified_file],
            ['删除文件中的快捷方式', self.delete_shortcut, en_file],
            ['删除文件末尾的.或省略号', self.delete_ellipsis, en_file],
            ['删除OmegaT翻译记忆文件中的快捷方式', self.delete_shortcut_of_omegat, 'data/project_save2.tmx'],
            ['删除OmegaT翻译记忆文件中的.或省略号', self.delete_ellipsis_of_omegat, 'data/project_save2.tmx'],
        ]
        iox.choose_action(action_list)

    def translate_file_by_reference(self, en_file, cn_file, result_file=None, untranslated_replace=None):
        """
        根据参考翻译文件
        :param en_file:英文
        :param cn_file: 参考中文
        :param result_file: 结果文件
        :param untranslated_replace:未翻译时替换
        :return:
        """
        if result_file is None:
            result_file = filex.get_result_file_name(en_file, '_translation_result')

        translation_dict = tool.get_dict_from_file(cn_file)
        result = self.translate_file_by_dict(en_file, translation_dict, untranslated_replace)

        filex.write_lines(result_file, result)

    @staticmethod
    def translate_file_by_dict(file_path, translation_dict, untranslated_replace=None):
        """
        翻译文件
        :param file_path: 要翻译的文件
        :param translation_dict: 字典
        :param untranslated_replace: 未翻译的用什么替换，（将会执行untranslated % (key_value[0], key_value[1])），
        如果执行失败则直接用其值替换
        默认为None，如果为None表示不替换
        :return:
        """
        lines = filex.read_lines(file_path)
        if lines is None:
            return None

        result = []
        untranslated_count = 0
        for line in lines:
            line = line.replace('\n', '')
            if '=' in line:
                key_value = line.split('=', 1)
                # 翻译
                key = key_value[0]
                if key in translation_dict.keys():
                    translation = translation_dict[key]
                    if translation is not None and translation != '':
                        line = '%s=%s' % (key_value[0], translation)
                else:
                    # line += '待翻译'
                    untranslated_count += 1
                    print('%d-%s-未翻译' % (untranslated_count, line))
                    if untranslated_replace is not None:
                        try:
                            line = untranslated_replace % (key_value[0], key_value[1])
                        except TypeError:
                            line = untranslated_replace
            result.append(line + '\n')
        return result

    @staticmethod
    def change_unicode_to_chinese(file_path, output_file=None):
        """
        将unicode转为中文
        :param file_path:源文件
        :param output_file: 输出文件
        :return:
        """
        if output_file is None:
            output_file = filex.get_result_file_name(file_path, '_cn_result')

        lines = filex.read_lines(file_path)
        if lines is None:
            return

        result = []
        for line in lines:
            line = line.replace('\n', '')
            if '=' in line:
                key_value = line.split('=', 1)
                line = '%s=%s' % (key_value[0], encodex.unicode_str_to_chinese(key_value[1]))
            result.append(line + '\n')
        filex.write_lines(output_file, result)

    @staticmethod
    def change_chinese_to_unicode(file_path, output_file=None):
        """
        将中文转为unicode
        :param file_path:
        :param output_file:
        :return:
        """
        if output_file is None:
            output_file = filex.get_result_file_name(file_path, '_unicode_result')

        lines = filex.read_lines(file_path)
        if lines is None:
            return

        result = []
        for line in lines:
            line = line.replace('\n', '')
            if '=' in line:
                key_value = line.split('=', 1)
                line = '%s=%s' % (key_value[0], encodex.chinese_to_unicode(key_value[1]))
            result.append(line + '\n')
        filex.write_lines(output_file, result)

    @staticmethod
    def convert_to_omegat_dict(en_file, cn_file, output_file=None):
        """
        将翻译结果转为omegaT的字典
        :param en_file: 英文文件
        :param cn_file: 中文文件
        :param output_file: 输出文件
        :return:
        """
        if output_file is None:
            output_file = filex.get_result_file_name(cn_file, '_omegat_result', 'xml')

        en_dict = tool.get_dict_from_file(en_file)
        cn_dict = tool.get_dict_from_file(cn_file)

        tmx = Et.Element('tmx')
        tmx.attrib['version'] = '1.1'
        Et.SubElement(tmx, 'header')
        body = Et.SubElement(tmx, 'body')
        for (k, v) in cn_dict.items():
            if k in en_dict.keys():
                en_value = en_dict[k]
                cn_value = v
                # 判断是否有多个句子，"."加一个空格
                added = False
                if '. ' in en_value:
                    en_split = en_value.split('. ')
                    if en_split[1] != '':
                        # 包含“.”，不是在最后的“...”
                        # 检查中文
                        if '。 ' in cn_value:
                            cn_split = cn_value.split('。 ')
                            if len(en_split) == len(cn_split):
                                added = True
                                # 中英长度相等
                                for i in range(len(en_split)):
                                    Tools.add_translate_element(body, en_split[i], cn_split[i])
                                    print('分开添加:' + cn_split[i])
                            else:
                                print('')
                                print(en_value)
                                print(cn_value)
                                print('%d,%d' % (len(en_split), len(cn_split)))
                        else:
                            print('')
                            print(en_value)
                            print(cn_value)
                            print('英文中有“. ”，中文中不包含“。 ”')
                if not added:
                    Tools.add_translate_element(body, en_value, cn_value)

        tree = Et.ElementTree(tmx)
        tree.write(output_file, encoding='utf-8')
        print('输出为' + output_file)

    @staticmethod
    def add_translate_element(element, en, cn):
        """
        向element中添加一个翻译
        :param element:
        :param en
        :param cn
        :return:
        """

        tu = Et.SubElement(element, 'tu')
        # 英文
        tuv = Et.SubElement(tu, 'tuv')
        tuv.attrib['lang'] = 'EN-US'
        seg = Et.SubElement(tuv, 'seg')
        seg.text = en
        # 中文
        tuv2 = Et.SubElement(tu, 'tuv')
        tuv2.attrib['lang'] = 'ZH-CN'
        seg2 = Et.SubElement(tuv2, 'seg')
        seg2.text = cn

    @staticmethod
    def process_file_for_translation(file, result_file=None):
        """
        在翻译前处理文件
        删除快捷方式
        删除末尾的.或省略号
        :param file:
        :param result_file:
        :return:
        """
        if result_file is None:
            result_file = filex.get_result_file_name(file, '_modified')
        print('删除省略号')
        Tools.delete_ellipsis(file, result_file)
        # 后面的将接着用result_fiel
        print('删除快捷方式')
        Tools.delete_shortcut(result_file, result_file)
        print('再次删除省略号，防止位于快捷方式之前')
        Tools.delete_ellipsis(result_file, result_file)

    @staticmethod
    def delete_shortcut(file, result_file=None):
        """
        删除文件中的快捷方式
        :param file:
        :param result_file:
        :return:
        """
        if result_file is None:
            result_file = filex.get_result_file_name(file, '_delete_shortcut')
        lines = filex.read_lines(file)
        if lines is None:
            return
        # (.*懒惰)(空白?点一次或多次)
        p = re.compile(r'(.*?)(\s?\(_\w\))')
        result = []
        for line in lines:
            line = line.replace('\n', '')
            if line is None:
                continue
            if '_' in line:
                if re.match(p, line) is not None:
                    replace_result = re.sub(p, r'\1', line)
                    print('删除【%s】为【%s】' % (line, replace_result))
                else:
                    replace_result = line.replace('_', '')
                    print('替换【%s】为【%s】' % (line, replace_result))
                line = replace_result
            result.append(line + '\n')

        filex.write_lines(result_file, result)

    @staticmethod
    def delete_ellipsis(file, result_file=None, print_msg=True):
        """
        删除每一行结尾的“.”，包括一个（句号）或多个（如省略号）
        :param file:
        :param result_file:
        :param print_msg:
        :return:
        """
        if result_file is None:
            result_file = filex.get_result_file_name(file, '_delete_ellipsis')
        lines = filex.read_lines(file)
        if lines is None:
            return
        # (.*懒惰)(空白?点一次或多次)
        p = re.compile(r'(.*?)(\s?(\.|。|…)+)$')
        result = []
        for line in lines:
            line = line.replace('\n', '')
            if line is None:
                continue
            if '.' in line:
                if re.match(p, line) is not None:
                    replace_result = re.sub(p, r'\1', line)
                    if print_msg:
                        print('删除【%s】为【%s】' % (line, replace_result))
                    line = replace_result
                else:
                    if print_msg:
                        pass
                        # print('未处理【%s】' % line)
            result.append(line + '\n')

        filex.write_lines(result_file, result)

    @staticmethod
    def delete_shortcut_of_omegat(file, result_file=None):
        """
        删除文件中的快捷方式，本来应该在导出的时候就删除，但是已经改了一些了，只好处理
        :param file:
        :param result_file:
        :return:
        """
        if result_file is None:
            result_file = filex.get_result_file_name(file, '_delete_shortcut')
        tree = Et.parse(file)
        tmx = tree.getroot()
        body = tmx.find('body')
        # (.*懒惰)(空白?\(下划线字母\))
        p = re.compile(r'(.*?)(\s?\(_\w\))')
        for seg in body.iter('seg'):
            content = seg.text
            if content is None:
                continue
            if '_' in content:
                if re.match(p, content) is not None:
                    replace_result = re.sub(p, r'\1', content)
                    print('删除【%s】为【%s】' % (content, replace_result))
                else:
                    replace_result = content.replace('_', '')
                    print('替换【%s】为【%s】' % (content, replace_result))
                seg.text = replace_result

        tree.write(result_file, encoding='utf-8')
        print('输出为' + result_file)

    @staticmethod
    def delete_ellipsis_of_omegat(file, result_file=None):
        """
        删除每一行结尾的“.”，包括一个（句号）或多个（如省略号）
        :param file:
        :param result_file:
        :return:
        """
        if result_file is None:
            result_file = filex.get_result_file_name(file, '_delete_ellipsis')
        tree = Et.parse(file)
        tmx = tree.getroot()
        body = tmx.find('body')
        # (.*懒惰)(空白?点一次或多次)
        p = re.compile(r'(.*?)(\s?\.+)$')
        for seg in body.iter('seg'):
            content = seg.text
            if content is None:
                continue
            if '.' in content:
                if re.match(p, content) is not None:
                    replace_result = re.sub(p, r'\1', content)
                    print('删除【%s】为【%s】' % (content, replace_result))
                else:
                    replace_result = content
                    print('未处理【%s】为【%s】' % (content, replace_result))
                seg.text = replace_result

        tree.write(result_file, encoding='utf-8')
        print('输出为' + result_file)


if __name__ == '__main__':
    Tools().main()
