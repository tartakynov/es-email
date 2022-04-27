import base64
import quopri
import re


# utf-7 decoding is based on http://www.php2python.com/wiki/function.imap-utf7-encode/
def modified_unbase64(s):
    s_utf7 = '+' + s.replace(',', '/') + '-'
    return s_utf7.encode().decode('utf-7')


def decode_imap4_utf7(s):
    r = list()
    if s.find('&-') != -1:
        s = s.split('&-')
        i = len(s)
        for subs in s:
            i -= 1
            r.append(decode_imap4_utf7(subs))
            if i != 0:
                r.append('&')
    else:
        # find what needs to be decoded
        regex = re.compile(r'[+]\S+?[-]')
        sym = re.split(regex, s)
        # if many substrings
        if len(regex.findall(s)) > 1:
            i = 0
            r.append(sym[i])
            for subs in regex.findall(s):
                r.append(decode_imap4_utf7(subs))
                i += 1
                r.append(sym[i])
        # only 1 substring
        elif len(regex.findall(s)) == 1:
            r.append(sym[0])
            r.append(modified_unbase64(regex.findall(s)[0][1:-1]))
            r.append(sym[1])
        # no need to decode
        else:
            r.append(s)
    return ''.join(r)


def _decode_mime_header_repl(match):
    charset, encoding, encoded_text = match.groups()
    if encoding == 'B':
        return base64.b64decode(encoded_text).decode(charset)
    elif encoding == 'Q':
        return quopri.decodestring(encoded_text).decode(charset)
    raise Exception(f'Unknown encoding: {encoding}')


def decode_mime_header(encoded_str):
    return re.sub(r'=\?([^?]+)\?([B|Q])\?([^?]+)\?=', _decode_mime_header_repl, encoded_str, flags=re.MULTILINE)
