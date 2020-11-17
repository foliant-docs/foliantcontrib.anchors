[![](https://img.shields.io/pypi/v/foliantcontrib.anchors.svg)](https://pypi.org/project/foliantcontrib.anchors/)  [![](https://img.shields.io/github/v/tag/foliant-docs/foliantcontrib.anchors.svg?label=GitHub)](https://github.com/foliant-docs/foliantcontrib.anchors)

# Anchors

Preprocessor which allows to use arbitrary anchors in Foliant documents.

## Installation

```bash
$ pip install foliantcontrib.anchors
```

## Config

To enable the preprocessor, add anchors to preprocessors section in the project config:

```yaml
preprocessors:
    - anchors
```

The preprocessor has some options, but most probably you won't need any of them:

```yaml
preprocessors:
    - anchors:
        element: '<span id="{anchor}"></span>'
        tex: False
```

`element`
:   Template of an HTML-element which will be placed instead of the `<anchor>` tag. In this template `{anchor}` will be replaced with the tag contents. Ignored when tex is `True`. Default: `'<span id="{anchor}"></span>'`

`tex`
:   If this option is `True`, preprocessor will try to use TeX-language anchors: `\hypertarget{anchor}{}`. Default: `False`

> Notice, this option will work only with `pdf` target. For all other targets it is set to `False`.

## Usage

Just add an `anchor` tag to some place and then use an ordinary Markdown-link to this anchor:

```html
...

<anchor>limitation</anchor>
Some important notice about system limitation.

...

Don't forget about [limitation](#limitation)!

```

You can also place anchors in the middle of paragraph:

```html

Lorem ipsum dolor sit amet, consectetur adipisicing elit.<anchor>middle</anchor> Molestiae illum iusto, sequi magnam consequatur porro iste facere at fugiat est corrupti dolorum quidem sapiente pariatur rem, alias unde! Iste, aliquam.

[Go to the middle of the paragraph](#middle)

```

You can place anchors inside tables:

```html

Name | Age | Weight
---- | --- | ------
Max  | 17  | 60
Jane | 98  | 12
John | 10  | 40
Katy | 54  | 54
Mike <anchor>Mike</anchor>| 22  | 299
Cinty| 25  | 42

...

Something's wrong with Mike, [look](#Mike)!

```

## Additional info

**1. Anchors are case sensitive**

`Markdown` and `MarkDown` are two different anchors.

**2. Anchors should be unique**

You can't use two anchors with the same name in one document.

If preprocessor notices repeating anchors in one md-file it will throw you a warning. If you are building a flat document (e.g. PDF or docx with Pandoc), you will receive the warning even if anchor repeats in different md-files.

**3. Anchors may conflict with headers**

Headers are usually assigned anchors of their own. Be careful, your anchors may conflict with them.

Preprocessor will try to detect if you are using anchor which is already taken by the header and warn you in console.

**4. Some symbols are restricted**

You can't use these symbols in anchors:

```
[]<>\"
```

Also you can't use space.

**5. But a lot of other symbols are available**

All these are valid anchors:

```
<anchor>!important!</anchor>
<anchor>_anchor_</anchor>
<anchor>section(1)</anchor>
<anchor>section/1/</anchor>
<anchor>anchor$1$</anchor>
<anchor>about:info</anchor>
<anchor>test'1';</anchor>
<anchor>якорь</anchor>
<anchor>👀</anchor>
```


## Notice for Mkdocs

In many Mkdocs themes the top menu lays over the text with absolute position. In this situation all anchors will be hidden by the menu.

Possible solution is to change the `element` option for your anchors to have a vertical offset. Example config:

```yaml
preprocessors:
    - anchors:
        element: '<span style="display:block; margin:-3.1rem; padding:3.1rem;" id="{anchor}"></span>'
```

Or, even better, you can assign your anchor a class in `element` and add these rules to your custom mkdocs styles.
