'''
Arbitrary anchors for Foliant.
'''

import re

from foliant.preprocessors.utils.combined_options import (CombinedOptions,
                                                          boolean_convertor)
from foliant.preprocessors.utils.preprocessor_ext import (BasePreprocessorExt,
                                                          allow_fail)
from foliant.preprocessors.utils.header_anchors import to_id, is_flat


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


def collect_header_anchors(text: str, backend: str) -> str:
    '''collect all headers in text and return dictionary {anchor: header}'''
    pattern = re.compile(r'^#{1,6} (.+?)(?=\n)', re.MULTILINE)
    headers = pattern.findall(text)
    return {to_id(h, backend): h for h in headers}


def fix_headers(text: str) -> str:
    '''add empty line after anchor if it goes before header'''
    pattern = r'(<anchor>.+?</anchor>\n)(#)'
    return re.sub(pattern, r'\1\n\2', text)


def get_span_anchor(anchor: str, options: CombinedOptions) -> str:
    return options['element'].format(anchor=anchor)


def get_tex_anchor(anchor: str) -> str:
    return r'\hypertarget{%s}{}' % anchor


def get_confluence_anchor(anchor: str) -> str:
    return f'''<raw_confluence><ac:structured-macro ac:macro-id="0" ac:name="anchor" ac:schema-version="1">
    <ac:parameter ac:name="">{anchor}</ac:parameter>
  </ac:structured-macro></raw_confluence>'''


class Preprocessor(BasePreprocessorExt):
    defaults = {
        'tex': False,
        'element': '<span id="{anchor}"></span>'
    }
    tags = ('anchor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.applied_anchors = []
        self.header_anchors = []

        self.logger = self.logger.getChild('anchors')

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    @allow_fail()
    def process_anchors(self, content: str) -> str:
        def _sub(block) -> str:
            anchor = block.group('body').strip()
            if anchor in self.applied_anchors:
                self._warning(f"Can't apply dublicate anchor \"{anchor}\", skipping.",
                              context=self.get_tag_context(block))
                return ''
            if anchor in self.header_anchors:
                self._warning(f'anchor "{anchor}" may conflict with header "{self.header_anchors[anchor]}".',
                              context=self.get_tag_context(block))
            options = CombinedOptions({'main': self.options,
                                       'tag': self.get_options(block.group('options'))},
                                      convertors={'tex': boolean_convertor},
                                      priority='tag')
            self.applied_anchors.append(anchor)
            if self.context['target'] == 'pdf' and options['tex']:
                return get_tex_anchor(anchor)
            elif self.context['target'] == 'confluence':
                return get_confluence_anchor(anchor)
            else:
                return get_span_anchor(anchor, options)
        return self.pattern.sub(_sub, content)

    def apply(self):
        self.logger.info('Applying preprocessor')

        for markdown_file_path in self.working_dir.rglob('*.md'):
            with open(markdown_file_path, encoding='utf8') as markdown_file:
                content = markdown_file.read()

            content = fix_headers(content)

            if not is_flat(self.context['backend']):
                self.applied_anchors = []
            self.header_anchors = collect_header_anchors(content, self.context['backend'])

            processed = self.process_anchors(content)

            with open(markdown_file_path, 'w', encoding='utf8') as markdown_file:
                markdown_file.write(processed)

        self.logger.info('Preprocessor applied')
