
from lxml import html
import requests
import re
import textwrap
import json
import os

class Paragraph:
    def __init__(self, text, is_code=False):
        self.text = textwrap.dedent(text)
        self.indent = get_indent_diff(text, self.text)
        self.is_code = is_code if is_code else self._find_code_pattern(text)
        self.is_toc = self._find_toc_pattern(text)
        # self.is_section_title = self._find_section_title_pattern(text)

        if self.is_toc:
            self.is_code = True
        if not self.is_code and not is_code:
            self.text = self.text.replace('\n', ' ') # 複数行を1行にまとめる

    def __str__(self):
        return 'Paragraph: level: %d, is_code: %s\n%s' % \
            (self.indent, self.is_code, self.text)

    def _find_code_pattern(self, text):
        return text.find('---') >= 0

    def _find_toc_pattern(self, text):
        return re.search(r'\.{5,}\d', text)

    def _find_section_title_pattern(self, text):
        return re.match(r'^\d+\.', text)


class Paragraphs:
    def __init__(self, text):
        is_header = True
        chunks = re.compile(r'\n\n+').split(text)
        self.paragraphs = []
        for i, chunk in enumerate(chunks):
            indent = get_indent(chunk)
            if i >= 1 and indent == 0:
                is_header = False

            flag = True if is_header or (indent - prev_indent > 3) else None
            self.paragraphs.append(Paragraph(chunk, is_code=flag))
            prev_indent = indent

    def __getitem__(self, key):
        return self.paragraphs[key]

    def __iter__(self):
        return iter(self.paragraphs)


def get_indent(text):
    return len(text) - len(text.lstrip())

def get_indent_diff(text1, text2):
    first_line1 = text1.split('\n')[0]
    first_line2 = text2.split('\n')[0]
    return abs(len(first_line1) - len(first_line2))


def fetch_rfc(number):

    url = 'https://tools.ietf.org/html/rfc%d' % number
    output_dir = 'data/%04d/%03d' % (round(number, -3), round(number, -2))
    output_file = '%s/rfc%d.json' % (output_dir, number)

    os.makedirs(output_dir, exist_ok=True)

    headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
        'referer': url,
    }
    page = requests.get(url, headers)
    tree = html.fromstring(page.content)

    contents = tree.xpath(
        '//pre/text() | ' # 本文
        '//pre/a/text() | ' # 本文中のリンク
        '//span[@class="h1" or @class="h2" or @class="h3" or '
               '@class="h4" or @class="h5" or @class="h6"]/text() |' # セクションのタイトル
        '//span/a[@class="selflink"]/text() |' # セクションの番号
        '//a[@class="invisible"]' # ページの区切り
    )

    for i, content in enumerate(contents):
        # ページ区切りのとき
        if (isinstance(content, html.HtmlElement) and
                content.get('class') == 'invisible'):

            contents[i-1] = contents[i-1].rstrip() # 前ページの末尾の空白を除去
            contents[i+0] = '' # ページ区切りの除去
            contents[i+1] = '' # 余分なノードの除去
            contents[i+2] = contents[i+2].lstrip('\n') # 次ページの先頭の改行を除去

            # ページをまたぐ文章に対応する処理
            first, last = 0, -1
            prev_last_line = contents[i-1].split('\n')[last]   # 前ページの最後の行
            next_first_line = contents[i+2].split('\n')[first] # 次ページの最初の行
            indent1 = get_indent(prev_last_line)
            indent2 = get_indent(next_first_line)
            if (not prev_last_line.endswith('.') and
                    indent1 != 0 and indent1 == indent2):
                # 内容がページをまたぐ場合、次ページの先頭の空白を1つにまとめる
                contents[i+2] = ' ' + contents[i+2].lstrip()
            else:
                # 内容がページをまたがない場合、ページの境界を明確にするために改行を挿入する
                contents[i+1] = '\n\n'

    contents[-1] = re.sub(r'.*\[Page \d+\]$', '', contents[-1].rstrip()).rstrip()
    text = ''.join(contents)

    paragraphs = Paragraphs(text)

    obj = []
    for paragraph in paragraphs:
        obj.append({
            'indent': paragraph.indent,
            'text': paragraph.text,
        })

    json_file = open(output_file, 'w')
    json.dump(obj, json_file, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('rfc_number', type=int)
    args = parser.parse_args()

    fetch_rfc(args.rfc_number)
