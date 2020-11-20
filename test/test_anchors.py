import os
import logging
from unittest import TestCase
from foliant_test.preprocessor import PreprocessorTestFramework


def rel_name(path: str):
    return os.path.join(os.path.dirname(__file__), path)


logging.disable(logging.CRITICAL)


class TestAnchors(TestCase):
    def setUp(self):
        self.ptf = PreprocessorTestFramework('anchors')

    def test_general(self):
        input_dir = rel_name('data/input')
        expected_dir = rel_name('data/expected_general')
        self.ptf.test_preprocessor(
            input_dir=input_dir,
            expected_dir=expected_dir
        )

    def test_flat(self):
        input_dir = rel_name('data/input')
        expected_dir = rel_name('data/expected_flat')
        self.ptf.context['backend'] = 'pandoc'
        self.ptf.test_preprocessor(
            input_dir=input_dir,
            expected_dir=expected_dir
        )

    def test_custom_ids(self):
        input_dir = rel_name('data/input')
        expected_dir = rel_name('data/expected_custom_ids')
        self.ptf.options = {'anchors': True, 'custom_ids': True}
        self.ptf.test_preprocessor(
            input_dir=input_dir,
            expected_dir=expected_dir
        )

    def test_only_anchors(self):
        input_map = {'index.md': '# My title {#custom_id}\n\nLorem ipsum <anchor>my_anchor</anchor> dolor sit, amet.'}
        expected_map = {'index.md': '# My title {#custom_id}\n\nLorem ipsum <span id="my_anchor"></span> dolor sit, amet.'}
        self.ptf.options = {'anchors': True, 'custom_ids': False}
        self.ptf.test_preprocessor(
            input_mapping=input_map,
            expected_mapping=expected_map,
        )

    def test_only_customids(self):
        input_map = {'index.md': '# My title {#custom_id}\n\nLorem ipsum <anchor>my_anchor</anchor> dolor sit, amet.'}
        expected_map = {'index.md': '<span id="custom_id"></span>\n\n# My title\n\nLorem ipsum <anchor>my_anchor</anchor> dolor sit, amet.'}
        self.ptf.options = {'anchors': False, 'custom_ids': True}
        self.ptf.test_preprocessor(
            input_mapping=input_map,
            expected_mapping=expected_map,
        )

    def test_none(self):
        input_map = {'index.md': '# My title {#custom_id}\n\nLorem ipsum <anchor>my_anchor</anchor> dolor sit, amet.'}
        self.ptf.options = {'anchors': False, 'custom_ids': False}
        self.ptf.test_preprocessor(
            input_mapping=input_map,
            expected_mapping=input_map,
        )

    def test_anchor_before_header(self):
        input_map = {'index.md': '<anchor>before_header</anchor>\n# My title\n\nLorem ipsum dolor sit, amet.'}
        expected_map = {'index.md': '<span id="before_header"></span>\n\n# My title\n\nLorem ipsum dolor sit, amet.'}
        self.ptf.test_preprocessor(
            input_mapping=input_map,
            expected_mapping=expected_map,
        )

    def test_confluence(self):
        input_map = {'index.md': '# My title\n\nLorem ipsum <anchor>my_anchor</anchor> dolor sit, amet.'}
        expected_map = {'index.md': '# My title\n\nLorem ipsum <raw_confluence><ac:structured-macro ac:macro-id="0" ac:name="anchor" ac:schema-version="1">\n    <ac:parameter ac:name="">my_anchor</ac:parameter>\n  </ac:structured-macro></raw_confluence> dolor sit, amet.'}
        self.ptf.options = {'anchors': True, 'custom_ids': False}
        self.ptf.context['target'] = 'confluence'
        self.ptf.test_preprocessor(
            input_mapping=input_map,
            expected_mapping=expected_map,
        )

    def test_confluence_overriden_element(self):
        input_map = {'index.md': '# My title\n\nLorem ipsum <anchor>my_anchor</anchor> dolor sit, amet.'}
        expected_map = {'index.md': '# My title\n\nLorem ipsum <div>my_anchor</div> dolor sit, amet.'}
        self.ptf.options = {'anchors': True, 'custom_ids': False, 'element': '<div>{anchor}</div>'}
        self.ptf.context['target'] = 'confluence'
        self.ptf.test_preprocessor(
            input_mapping=input_map,
            expected_mapping=expected_map,
        )
