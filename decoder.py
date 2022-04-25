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


def decode_encoded_words(encoded_str):
    match = re.search(r'=\?(.+)\?([B|Q])\?(.+)\?=', encoded_str, re.MULTILINE)
    if not match:
        return encoded_str
    charset, encoding, encoded_text = match.groups()
    left, right = match.span()
    byte_string = encoded_str[:left]
    if encoding == 'B':
        byte_string += base64.b64decode(encoded_text).decode(charset)
    elif encoding == 'Q':
        byte_string += quopri.decodestring(encoded_text).decode(charset)
    byte_string += encoded_str[right:]
    return byte_string


def decode_base64(value):
    return base64.b64decode(value)
