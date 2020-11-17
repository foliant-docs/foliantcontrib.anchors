'''
Arbitrary anchors for Foliant.
'''

import re

from foliant.preprocessors.utils.combined_options import (CombinedOptions,
                                                          boolean_convertor)
from foliant.preprocessors.utils.preprocessor_ext import (BasePreprocessorExt,
                                                          allow_fail)
from foliant.preprocessors.utils.header_anchors import to_id, is_flat


def collect_header_anchors(text: str, backend: str) -> str:
    '''collect all headers in text and return dictionary {anchor: header}'''
    pattern = re.compile(r'^#{1,6} (.+?)(?=\n)', re.MULTILINE)
    headers = pattern.findall(text)
    return {to_id(h, backend): h for h in headers}


def fix_headers(text: str) -> str:
    '''add empty line after anchor if it goes before header'''
    pattern = r'(<anchor>.+?</anchor>\n)(#)'
    return re.sub(pattern, r'\1\n\2', text)


def get_tex_anchor(anchor: str) -> str:
    return r'\hypertarget{%s}{}' % anchor


def get_anchor(anchor: str, options: CombinedOptions, target: str):
    default_templates = {
        'default': '<span id="{anchor}"></span>',
        'confluence':
            '''<raw_confluence><ac:structured-macro ac:macro-id="0" ac:name="anchor" ac:schema-version="1">
    <ac:parameter ac:name="">{anchor}</ac:parameter>
  </ac:structured-macro></raw_confluence>'''
    }
    if 'element' in options:
        # element is customized, using user template
        return options['element'].format(anchor=anchor)
    else:
        template = default_templates.get(target, default_templates['default'])
        return template.format(anchor=anchor)


class Preprocessor(BasePreprocessorExt):
    defaults = {
        'tex': False,
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
            else:
                return get_anchor(options, self.context['target'])
        return self.pattern.sub(_sub, content)

    def process_file(self, content: str) -> str:
        processed_content = fix_headers(content)
        if not is_flat(self.context['backend']):
            self.applied_anchors = []
        self.header_anchors = collect_header_anchors(content, self.context['backend'])
        return self.process_anchors(processed_content)

    def apply(self):
        self._process_all_files(self.process_file)
        self.logger.info('Preprocessor applied')
