'''
Arbitrary anchors for Foliant.
'''

import re

from foliant.preprocessors.base import BasePreprocessor
from foliant.utils import output

from foliant.preprocessors.utils.combined_options import (CombinedOptions,
                                                          boolean_convertor)

OptionValue = int or float or bool or str


def convert_to_anchor(reference: str) -> str:
    '''
    Convert reference string into correct anchor

    >>> convert_to_anchor('GET /endpoint/method{id}')
    'get-endpoint-method-id'
    '''

    result = ''
    accum = False
    header = reference
    for char in header:
        if char == '_' or char.isalpha():
            if accum:
                accum = False
                result += f'-{char.lower()}'
            else:
                result += char.lower()
        else:
            accum = True
    return result.strip(' -')


class Preprocessor(BasePreprocessor):
    defaults = {
        'tex': False,
        'element': '<span id="{anchor}"></span>'
    }
    tags = ('anchor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = self.logger.getChild('graphviz')

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    def _collect_header_anchors(self, text):
        '''collect all headers in text and return dictionary {anchor: header}'''
        pattern = r'^#+ (.+)'
        headers = re.findall(pattern, text, re.MULTILINE)
        if not headers:
            return {}
        return {convert_to_anchor(h): h for h in headers}

    def _fix_headers(self, text):
        '''adds empty line after anchor if it goes before header'''
        pattern = r'(<anchor>.+?</anchor>\n)(#)'
        return re.sub(pattern, r'\1\n\2', text)

    def _get_span_anchor(self, anchor: str, options: CombinedOptions) -> str:
        return options['element'].format(anchor=anchor)

    def _get_tex_anchor(self, anchor: str) -> str:
        return r'\hypertarget{%s}{}' % anchor

    def process_anchors(self, content: str) -> str:

        def _sub(block) -> str:
            anchor = block.group('body').strip()
            if anchor in self.applied_anchors:
                output(f"WARNING: Can't apply dublicate anchor \"{anchor}\", skipping.",
                       quiet=self.quiet)
                return ''
            if anchor in self.header_anchors:
                output(f'WARNING: anchor "{anchor}" may conflict with header '
                       f'"{self.header_anchors[anchor]}".', quiet=self.quiet)
            options = CombinedOptions({'main': self.options,
                                       'tag': self.get_options(block.group('options'))},
                                      convertors={'tex': boolean_convertor},
                                      priority='tag')
            self.applied_anchors.append(anchor)
            if self.context['target'] == 'pdf' and options['tex']:
                return self._get_tex_anchor(anchor)
            else:
                return self._get_span_anchor(anchor, options)
        return self.pattern.sub(_sub, content)

    def apply(self):
        self.logger.info('Applying preprocessor')

        for markdown_file_path in self.working_dir.rglob('*.md'):
            with open(markdown_file_path, encoding='utf8') as markdown_file:
                content = markdown_file.read()

            content = self._fix_headers(content)

            self.applied_anchors = []
            self.header_anchors = self._collect_header_anchors(content)

            processed = self.process_anchors(content)

            with open(markdown_file_path, 'w', encoding='utf8') as markdown_file:
                markdown_file.write(processed)

        self.logger.info('Preprocessor applied')
