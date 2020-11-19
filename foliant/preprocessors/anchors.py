'''
Arbitrary anchors for Foliant.
'''

import re

from foliant.preprocessors.utils.combined_options import (CombinedOptions, Options,
                                                          boolean_convertor)
from foliant.preprocessors.utils.preprocessor_ext import (BasePreprocessorExt,
                                                          allow_fail)
from foliant.preprocessors.utils.header_anchors import is_flat, IDGenerator
from foliant.contrib.chapters import Chapters


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


def contains_illegal_chars(text):
    illegal_chars = '[]<>\\" '
    for char in illegal_chars:
        if char in text:
            return char


class Preprocessor(BasePreprocessorExt):
    defaults = {
        'tex': False,
        'anchors': True,
        'custom_ids': False
    }
    tags = ('anchor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.applied_anchors = []
        self.header_anchors = {}
        self.customids_pattern = re.compile(
            r'^(?P<heading>\#{1,6}\s+.*\S+)\s+\{\#(?P<custom_id>\S+)\}\s*$',
            flags=re.MULTILINE
        )
        self.chapters = Chapters.from_config(self.config)

        self.logger = self.logger.getChild('anchors')

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    @allow_fail()
    def process_anchors(self, content: str, header_anchors: dict) -> str:
        def _sub(block) -> str:
            anchor = block.group('body').strip()
            if anchor in self.applied_anchors:
                self._warning(f"Can't apply dublicate anchor \"{anchor}\", skipping.",
                              context=self.get_tag_context(block))
                return ''
            if anchor in header_anchors:
                self._warning(f'anchor "{anchor}" may conflict with header "{header_anchors[anchor]}".',
                              context=self.get_tag_context(block))
            options = CombinedOptions({'main': self.options,
                                       'tag': self.get_options(block.group('options'))},
                                      convertors={'tex': boolean_convertor},
                                      priority='tag')

            illegal_char = contains_illegal_chars(anchor)
            if illegal_char:
                self._warning(f"Can't apply anchor \"{anchor}\", because it contains illegal symbol: {illegal_char}.",
                              context=self.get_tag_context(block))
                return ''

            self.applied_anchors.append(anchor)

            if self.context['target'] == 'pdf' and options['tex']:
                return get_tex_anchor(anchor)
            else:
                return get_anchor(anchor, options, self.context['target'])
        return self.pattern.sub(_sub, content)

    @allow_fail()
    def process_customids(self, content: str, header_anchors: dict) -> str:
        def _sub(block) -> str:
            custom_id = block.group('custom_id').strip()
            if custom_id in self.applied_anchors:
                self._warning(f"Can't apply dublicate custom ID \"{custom_id}\", skipping.",
                              context=self.get_tag_context(block))
                return ''
            if custom_id in header_anchors:
                self._warning(f'Custom ID "{custom_id}" may conflict with header "{header_anchors[custom_id]}".',
                              context=self.get_tag_context(block))
            options = Options(self.options)

            illegal_char = contains_illegal_chars(custom_id)
            if illegal_char:
                self._warning(f"Can't apply custom ID \"{custom_id}\", because it contains illegal symbol: {illegal_char}.",
                              context=self.get_tag_context(block))
                return ''

            self.applied_anchors.append(custom_id)

            if self.context['target'] == 'pdf' and options['tex']:
                element = get_tex_anchor(custom_id)
            else:
                element = get_anchor(custom_id, options, self.context['target'])

            return f'{element}\n\n{block.group("heading")}\n'
        return self.customids_pattern.sub(_sub, content)

    def collect_header_anchors(self) -> str:
        '''collect all headers in text and return dictionary {anchor: header}'''
        header_pattern = re.compile(r'^#{1,6} (?P<heading>.+?)(?P<customid>\{\#\S+\})?\s*$', re.MULTILINE)
        idgen = IDGenerator(self.context['backend'])
        self.header_anchors = {'overall': {}}
        for chapter in self.chapters.paths(self.chapters.working_dir):
            chapter_anchors = {}
            with open(chapter, encoding='utf8') as f:
                chapter_source = f.read()
            for header in header_pattern.finditer(chapter_source):
                heading = header.group('heading')
                chapter_anchors[idgen.generate(heading)] = heading
            self.header_anchors[chapter.resolve().as_posix()] = chapter_anchors
            if is_flat(self.context['backend']):
                self.header_anchors['overall'].update(chapter_anchors)
            else:
                idgen.reset()
        # return {self.idgen.generate(h): h for h in headers}

    def process_file(self, content: str) -> str:
        processed_content = fix_headers(content)
        if is_flat(self.context['backend']):
            header_anchors = self.header_anchors['overall']
        else:
            header_anchors = self.header_anchors.get(self.current_filepath.resolve().as_posix(), {})
            self.applied_anchors = []

        if self.options['custom_ids']:
            processed_content = self.process_customids(processed_content, header_anchors)
        if self.options['anchors']:
            processed_content = self.process_anchors(processed_content, header_anchors)
        return processed_content

    def apply(self):
        self.collect_header_anchors()
        self.logger.debug(f'Collected header anchors for chapters:\n{self.header_anchors}')
        self._process_all_files(self.process_file)
        self.logger.info('Preprocessor applied')
