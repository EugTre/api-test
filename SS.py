import utils.matchers as match

HEADERS_SIMPLE = {
    "Accept": "text/plain, text/html, text/x-dvi",
    "Accept-Charset": "iso-8859-5, Unicode-1-1"
}

#headers={
#    "Accept": AnyTextLike("Text/plain, Text/html, Text/x-dvi"),
#    "Accept-Charset": AnyTextLike("iso-8859-5, unicode-1-1", case_sensitive=True)
#}


def test():
    assert match.AnyText() == HEADERS_SIMPLE, 'stuff'
