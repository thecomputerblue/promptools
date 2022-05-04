import tkhtmlview

# plug the transposed doc between these
HTML_HEADER = \
"""<!DOCTYPE html>
    <html>
        <head>
            <title>PromptoolsExport</title>
        <head>
        <body>
        """
SIZE = 70
SIZE_HEADER = f'<p style="font-size:{SIZE}px;"">'
HTML_FOOTER = "</p></body></html>"

excluded = ('size')

def tkt_to_html_simple(tkt):
    """Convert tkt to simple html without preserving special formatting."""

    # dump tags & text to body to be combined at end.
    body = []

    for tup in tkt:
        pos, tag, word = tup
        if tag not in excluded:
            body.append('<br>') if tag == 'nl' else body.append(word)

    return format_body(''.join(body))

def format_body(body):
    return HTML_HEADER + SIZE_HEADER + body + HTML_FOOTER

"""
TODOS
- doesn't preserve whitespace.
"""
