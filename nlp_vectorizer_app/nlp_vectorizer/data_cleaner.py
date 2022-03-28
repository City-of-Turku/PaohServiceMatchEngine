import re
import unicodedata
from functools import reduce


class DataCleaner():
    """
    A class used to clean text from urls, phone numbers, weird chars etc.


    Methods
    -------
    clean_text(text: str)
        Returns cleaned text
    """

    def __init__(self) -> None:
        self.url_regex = re.compile(
            r'((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))')
        self.control_char_regex = re.compile(r'[\r\n\t]+')
        self.phone_number_regex = re.compile('\(?\+?\d[\s\d()-]{5,}\d')
        self.id_regex = re.compile('\d{6}[-+Aa]\d{3}[a-zA-Z0-9]')
        self.email_regex = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')

    def clean_text(self, text: str) -> str:
        data_preprocessing_funcs = [self._replace_identity, self._replace_phone_number, self._replace_url, self._replace_email,
                                    self._fix_html, self._standardise_punc, self._remove_unicode_symbols,
                                    self._remove_control_char, self._remove_remaining_control_chars,
                                    self._remove_multi_space]
        return reduce(lambda x, y: y(x), data_preprocessing_funcs, text)

    def _standardise_punc(self, text: str) -> str:
        transl_table = dict([(ord(x), ord(y))
                             for x, y in zip(u"‘’´“”–-",  u"'''\"\"--")])
        text_mod = text.translate(transl_table)
        text_mod = re.sub(
            r"[^a-zA-Z0-9À-ÿ .,'%&€$=@+;<>/()!?%:-]", " ", text_mod)
        return (text_mod)

    def _remove_control_char(self, text: str) -> str:
        text_mod = re.sub(self.control_char_regex, ' ', text)
        return (text_mod)

    def _remove_remaining_control_chars(self, text: str) -> str:
        text_mod = ''.join(
            ch for ch in text if unicodedata.category(ch)[0] != 'C')
        return (text_mod)

    def _remove_multi_space(self, text: str) -> str:
        text_mod = ' '.join(text.split())
        return (text_mod)

    def _remove_unicode_symbols(self, text: str) -> str:
        text_mod = ''.join(
            ch for ch in text if unicodedata.category(ch)[0:2] != 'So')
        return (text_mod)

    def _replace_url(self, text: str) -> str:
        filler = ''
        occ = text.count('www.') + text.count('http:') + text.count('https:')
        for _ in range(occ):
            # replace other urls by filler
            text = re.sub(self.url_regex, filler, text)
            text = ' '.join(text.split())
        return(text)

    def _fix_html(self, text: str) -> str:
        "From fastai: 'Fix messy things we've seen in documents'"
        text_mod = text.replace('#39;', "'").replace('amp;', '&').replace('#146;', "'").replace('nbsp;', ' ').replace('\\n', "\n").replace(
            'quot;', "'").replace('<br />', "\n").replace('\\"', '"').replace(' @.@ ', '.').replace(' @-@ ', '-').replace('...', ' …')
        return (text_mod)

    def _replace_phone_number(self, text: str) -> str:
        text_mod = re.sub(self.phone_number_regex, ' ', text)
        return (text_mod)

    def _replace_identity(self, text: str) -> str:
        text_mod = re.sub(self.id_regex, ' ', text)
        return (text_mod)

    def _replace_email(self, text: str) -> str:
        text_mod = re.sub(self.email_regex, ' ', text)
        return (text_mod)
