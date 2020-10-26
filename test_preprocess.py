import string

from nose.tools import assert_equal

from th_preprocessor.preprocess import (
    insert_spaces,
    is_date_str,
    is_datetime_str,
    is_latin_str,
    is_number_str,
    is_thai_str,
    normalize_at_mention,
    normalize_email,
    normalize_emoji,
    normalize_haha,
    normalize_link,
    normalize_num,
    normalize_phone,
    normalize_text_pairs,
    preprocess,
    remove_dup_spaces,
    remove_emoji,
    remove_others_char,
    remove_tag,
    replace_rep_after,
)


class Test_preprocess(object):
    def __init__(self):
        self.date_text = "2020-02-02"
        self.datetime_text = "2020-02-02 15:14:13"
        self.number_text = "3"
        self.number_longer_text = "1234"
        self.latin_text = "ABCD1234"
        self.thai_text = "อยู่คนเดียวได้บ้างแล้ว"
        self.mix_text = "hey123ไม่ได้เป็นคนที่เกเร"
        self.unnorm_text = "เเําฤาฦา๑๒๓๔๕๖๗๘๙๐,.=\0\r\n\t\u00A0" + string.punctuation
        self.link_text = "http://www.youtube.com"
        self.mention_text = "@test1234"
        self.email_text = "test_eiei_za@gmail.com"
        self.haha_text = "555555"
        self.phone_text = "0123456789"
        self.tag_text = "<div>Test HTML</div>"
        self.dup_space_text = "นอนได้แล้ว\n\n\n\n\nเดี๋ยวพรุ่งนี้เขาก็กลับมา"
        self.emoji_text = "🌈อย่าฟอล เดี๋ยวจน🌻รีวิวในแท็ก"
        self.noodle_text = "˚┉┉┉┉┉༝✧ คิดว่าน่าจะเหลือแค่ภาษาไทย กับ ˢʰᵉ 𝙧𝙖𝙩𝙘𝙝𝙖𝙙𝙖𝙥𝙞𝙨𝙚𝙠 English และ  ﾏﾝﾎﾞﾏﾝﾎﾞ．．．ນະຄອນຫລ🤔🤔🤔🤔ວງ．ﺍﻟﻘﻔﺺ🤣"
        self.complex_text = " ".join(
            [
                self.tag_text,
                self.link_text,
                self.mention_text,
                self.email_text,
                "&amp;",
                self.phone_text,
                self.unnorm_text,
                self.mix_text,
                self.haha_text,
                self.emoji_text,
                self.number_text,
                self.noodle_text,
            ]
        )
        self.real_text = 'Updated ประกาศเตือนภัย&nbsp;&nbsp;ออกเมื่อพฤหัสที่ 3&nbsp;&nbsp;เวลา 04:00 น.<br />\n<a href="https://www.tmd.go.th/programs//uploads/announces/2019-01-03_06014.pdf" rel="nofollow" target="_blank" >https://www.tmd.go.th/programs//uploads/announces/2019-01-03_06014.pdf</a><br />\n<img class="img-in-post" src="https://f.ptcdn.info/755/061/000/pkqdd02d0qwDpjgs6mFQ-o.png" data-image="img:800x508" /><br />\n<br />\nUpdated การพยากรณ์เส้นทางพายุ&nbsp;&nbsp;ออกโดยกรมอุตุ ฯ&nbsp;&nbsp;เมื่อพฤหัสที่ 3&nbsp;&nbsp;เวลา 05:00 น. ครับ<br />\n<img class="img-in-post" src="https://f.ptcdn.info/755/061/000/pkqdfu1dt286fsVcGubK-o.png" data-image="img:815x594" />'
        self.dup_text = (
            "เพราะว่าเธออออออออและเขา ถ่านนนนนนนนไฟเก่ายังร้อนรอวันรื้อฟื้นนนนนนนนน"
        )

    def test_is_date_str(self):
        assert_equal(is_date_str(self.date_text), True)

    def test_is_datetime_str(self):
        assert_equal(is_datetime_str(self.datetime_text), True)

    def test_is_number_str(self):
        assert_equal(is_number_str(self.number_text), True)

    def test_is_latin_str(self):
        assert_equal(is_latin_str(self.latin_text), True)

    def test_is_not_only_latin_str(self):
        assert_equal(is_latin_str(self.mix_text), False)

    def test_is_thai_str(self):
        assert_equal(is_thai_str(self.thai_text), True)

    def test_is_not_only_thai_str(self):
        assert_equal(is_thai_str(self.mix_text), False)

    def test_normalize_text_pairs(self):
        expected_result = "แำฤๅฦๅ1234567890         !                     ?            "
        assert_equal(normalize_text_pairs(self.unnorm_text), expected_result)

    def test_normalize_link(self):
        expected_result = " WSLINK "
        assert_equal(normalize_link(self.link_text), expected_result)

    def test_normalize_at_mention(self):
        expected_result = " WSNAME "
        assert_equal(normalize_at_mention(self.mention_text), expected_result)

    def test_normalize_email(self):
        expected_result = " WSEMAIL "
        assert_equal(normalize_email(self.email_text), expected_result)

    def test_normalize_haha(self):
        expected_result = " WSHAHA "
        assert_equal(normalize_haha(self.haha_text), expected_result)

    def test_normalize_num(self):
        expected_result = " WSNUMBER "
        assert_equal(normalize_num(self.number_text), expected_result)

    def test_normalize_num_longer(self):
        expected_result = " WSNUMBER "
        assert_equal(normalize_num(self.number_longer_text), expected_result)

    def test_normalize_phone(self):
        expected_result = " WSPHONE "
        assert_equal(normalize_phone(self.phone_text), expected_result)

    def test_remove_tag(self):
        expected_result = "Test HTML"
        assert_equal(remove_tag(self.tag_text), expected_result)

    def test_remove_dup_chars(self):
        expected_result = "นอนได้แล้ว\nเดี๋ยวพรุ่งนี้เขาก็กลับมา"
        assert_equal(remove_dup_spaces(self.dup_space_text), expected_result)

    def test_insert_spaces(self):
        expected_result = "hey 123 ไม่ได้เป็นคนที่เกเร"
        assert_equal(insert_spaces(self.mix_text), expected_result)

    def test_remove_emoji(self):
        expected_result = "อย่าฟอล เดี๋ยวจนรีวิวในแท็ก"
        assert_equal(remove_emoji(self.emoji_text), expected_result)

    def test_normalize_emoji(self):
        expected_result = "🌈 อย่าฟอล เดี๋ยวจน 🌻 รีวิวในแท็ก"
        assert_equal(normalize_emoji(self.emoji_text), expected_result)

    def test_preprocess(self):
        expected_result = "test html WSLINK WSNAME WSEMAIL WSPHONE แำฤๅฦๅ WSNUMBER ! ? hey WSNUMBER ไม่ได้เป็นคนที่เกเร WSHAHA 🌈 อย่าฟอล เดี๋ยวจน 🌻 รีวิวในแท็ก WSNUMBER คิดว่าน่าจะเหลือแค่ภาษาไทย กับ english และ 🤔 🤔 🤔 🤔 🤣"
        assert_equal(preprocess(self.complex_text), expected_result)

    def test_preprocess_real_text(self):
        expected_result = "updated ประกาศเตือนภัย ออกเมื่อพฤหัสที่ WSNUMBER เวลา WSNUMBER WSNUMBER น WSLINK updated การพยากรณ์เส้นทางพายุ ออกโดยกรมอุตุ ฯ เมื่อพฤหัสที่ WSNUMBER เวลา WSNUMBER WSNUMBER น ครับ"
        assert_equal(preprocess(self.real_text), expected_result)

    def test_remove_others_char(self):
        expected_result = "         คิดว่าน่าจะเหลือแค่ภาษาไทย กับ                   English และ                    🤔🤔🤔🤔        🤣"
        assert_equal(remove_others_char(self.noodle_text), expected_result)

    def test_replace_rep_after(self):
        expected_result = "เพราะว่าเธอและเขา ถ่านไฟเก่ายังร้อนรอวันรื้อฟื้น"
        assert_equal(replace_rep_after(self.dup_text), expected_result)
