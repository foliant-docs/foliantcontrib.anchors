import os
from unittest import TestCase
from foliant.contrib.test_framework import PreprocessorTestFramework


def rel_name(path: str):
    return os.path.join(os.path.dirname(__file__), path)


class TestAnchors(TestCase):
    def setUp(self):
        self.ptf = PreprocessorTestFramework('anchors')
        print(__file__)

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
