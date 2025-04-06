# utils/formatter.py
import jsbeautifier

def beautify_code(html: str, css: str):
    opts = jsbeautifier.default_options()
    opts.indent_size = 2
    return {
        "html": jsbeautifier.beautify(html, opts),
        "css": jsbeautifier.beautify(css, opts)
    }
