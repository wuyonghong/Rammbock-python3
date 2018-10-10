from unittest import TestCase, main
from Rammbock.templates.primitives import Char, UInt, PDU, Binary, Int
from Rammbock.message import Field
from Rammbock.binary_tools import to_bin


class TestTemplateFields(TestCase):

    def test_int_static_field(self):
        field = Int('4', "field", '-72')
        self.assertTrue(field.length.static)
        self.assertEqual(field.name, "field")
        self.assertEqual(field.default_value, '-72')
        self.assertEqual(field.type, 'int')
        self.assertEqual(field.encode({}, {}, None).hex, '0xffffffb8')

    def test_uint_static_field(self):
        field = UInt(5, "field", 8)
        self.assertTrue(field.length.static)
        self.assertEqual(field.name, "field")
        self.assertEqual(field.default_value, '8')
        self.assertEqual(field.type, 'uint')
        self.assertEqual(field.encode({}, {}, None).hex, '0x0000000008')

    def test_char_static_field(self):
        field = Char(5, "char_field", 'foo')
        self.assertTrue(field.length.static)
        self.assertEqual(field.name, "char_field")
        self.assertEqual(field.default_value, 'foo')
        self.assertEqual(field.type, 'chars')
        self.assertEqual(field.encode({}, {}, None)._raw, 'foo\x00\x00')
        self.assertEqual(field.encode({}, {}, None).bytes, 'foo\x00\x00')

    def test_set_char_value_from_message_field(self):
        msg_field = Field('chars', 'char_field', '\x00a\x00b', aligned_len=5)
        field = Char(5, "char_field", '')
        self.assertEqual(field.encode({'char_field': msg_field}, {}, None)._raw, '\x00a\x00b\x00')
        self.assertEqual(field.encode({'char_field': msg_field}, {}, None).bytes, '\x00a\x00b\x00')

    def test_binary_field(self):
        field = Binary(3, 'field', 1)
        self.assertTrue(field.length.static)
        self.assertEqual(field.name, "field")
        self.assertEqual(field.default_value, '1')
        self.assertEqual(field.type, 'bin')
        self.assertEqual(field.encode({}, {}, None).hex, '0x01')

    def test_long_binary_field_value(self):
        field = Binary(23, 'field', '0b1 1111 1111')
        self.assertEqual(field.encode({}, {}, None).hex, '0x0001ff')

    def test_binary_field_length_must_be_static(self):
        self.assertRaises(AssertionError, Binary, 'length', 'field', None)

    def test_encoding_missing_value_fails(self):
        field = UInt(2, 'foo', None)
        self.assertRaises(Exception, field.encode, {}, {})
        field = UInt(2, 'foo', '')
        self.assertRaises(Exception, field.encode, {}, {})

    def test_encoding_illegal_value_fails(self):
        field = UInt(2, 'foo', '(1|2)')
        self.assertRaises(Exception, field.encode, {}, {})
        field = UInt(2, 'foo', 'poplpdsf')
        self.assertRaises(Exception, field.encode, {}, {})

    def test_pdu_field_without_subtractor(self):
        field = PDU('value')
        self.assertEqual(field.length.field, 'value')
        self.assertEqual(field.length.calc_value(0), 0)
        self.assertEqual(field.type, 'pdu')

    def test_pdu_field_with_subtractor(self):
        field = PDU('value-8')
        self.assertEqual(field.length.field, 'value')
        self.assertEqual(field.length.calc_value(8), 0)

    def test_decode_uint(self):
        field_template = UInt(2, 'field', 6)
        decoded = field_template.decode(to_bin('0xcafe'), {})
        self.assertEqual(decoded.hex, '0xcafe')

    def test_decode_int(self):
        field_template = Int(2, 'field', -72)
        decoded = field_template.decode(to_bin('0xffb8'), {})
        self.assertEqual(decoded.int, -72)
        self.assertEqual(decoded.hex, '0xffb8')

    def test_decode_chars(self):
        field_template = Char(2, 'field', 6)
        decoded = field_template.decode(to_bin('0xcafe'), {})
        self.assertEqual(decoded.hex, '0xcafe')

    def test_decode_returns_used_length(self):
        field_template = UInt(2, 'field', 6)
        data = to_bin('0xcafebabeff00ff00')
        decoded = field_template.decode(data, {})
        self.assertEqual(decoded.hex, '0xcafe')
        self.assertEqual(len(decoded), 2)


class TestLittleEndian(TestCase):

    def test_little_endian_uint_decode(self):
        template = UInt(2, 'field', None)
        field = template.decode(to_bin('0x0100'), None, little_endian=True)
        self.assertEqual(field._raw, to_bin('0x0100'))
        self.assertEqual(field.int, 1)
        self.assertEqual(field.bytes, to_bin('0x0001'))

    def test_little_endian_int_decode(self):
        template = Int(2, 'field', None)
        field = template.decode(to_bin('0xb8ff'), None, little_endian=True)
        self.assertEqual(field._raw, to_bin('0xb8ff'))
        self.assertEqual(field.int, -72)
        self.assertEqual(field.bytes, to_bin('0xffb8'))

    def test_little_endian_char_decode(self):
        template = Char(5, 'field', None)
        field = template.decode('hello', None, little_endian=True)
        self.assertEqual(field._raw, 'hello')
        self.assertEqual(field.bytes, 'hello')
        self.assertEqual(field.ascii, 'hello')

    def test_little_endian_uint_encode(self):
        template = UInt(2, 'field', 1)
        field = template.encode({}, {}, None, little_endian=True)
        self.assertEqual(field._raw, to_bin('0x0100'))
        self.assertEqual(field.int, 1)
        self.assertEqual(field.bytes, to_bin('0x0001'))

    def test_little_endian_int_encode(self):
        template = Int(2, 'field', -72)
        field = template.encode({}, {}, None, little_endian=True)
        self.assertEqual(field._raw, to_bin('0xb8ff'))
        self.assertEqual(field.int, -72)
        self.assertEqual(field.bytes, to_bin('0xffb8'))


class TestTemplateFieldValidation(TestCase):

    def test_validate_uint(self):
        field = Field('uint', 'field', to_bin('0x0004'))
        self._should_pass(UInt(2, 'field', 4).validate({'field': field}, {}))
        self._should_pass(UInt(2, 'field', '4').validate({'field': field}, {}))
        self._should_pass(UInt(2, 'field', '0x04').validate({'field': field}, {}))
        self._should_pass(UInt(2, 'field', '0x0004').validate({'field': field}, {}))
        self._should_pass(UInt(2, 'field', '(0|4)').validate({'field': field}, {}))
        self._should_fail(UInt(2, 'field', 'REGEXP:.*').validate({'field': field}, {}), 1)

    def test_validate_int(self):
        field = Field('int', 'field', to_bin('0xffb8'))
        self._should_pass(Int(2, 'field', -72).validate({'field': field}, {}))
        self._should_pass(Int(2, 'field', '-72').validate({'field': field}, {}))
        self._should_pass(Int(2, 'field', '-0x48').validate({'field': field}, {}))
        self._should_pass(Int(2, 'field', '-0x0048').validate({'field': field}, {}))
        self._should_pass(Int(2, 'field', '(0|-72)').validate({'field': field}, {}))
        self._should_fail(Int(2, 'field', 'REGEXP:.*').validate({'field': field}, {}), 1)

    def test_validate_chars(self):
        field = Field('chars', 'field', 'foo\x00\x00')
        field_regEx = Field('chars', 'field', '{ Message In Braces }')
        self._should_pass(Char(5, 'field', 'foo').validate({'field': field}, {}))
        self._should_pass(Char(5, 'field', '(what|foo|bar)').validate({'field': field}, {}))
        self._should_pass(Char(5, 'field', 'REGEXP:^{[a-zA-Z ]+}$').validate({'field': field_regEx}, {}))
        self._should_pass(Char(5, 'field', 'REGEXP:^foo').validate({'field': field}, {}))
        self._should_pass(Char(5, 'field', 'REGEXP:').validate({'field': field}, {}))
        self._should_fail(Char(5, 'field', 'REGEXP:^abc').validate({'field': field}, {}), 1)

    def _should_pass(self, validation):
        self.assertEqual(validation, [])

    def _should_fail(self, validation, number_of_errors):
        self.assertEqual(len(validation), number_of_errors)

    def test_fail_validating_uint(self):
        template = UInt(2, 'field', 4)
        field = Field('uint', 'field', to_bin('0x0004'))
        self._should_fail(template.validate({'field': field}, {'field': '42'}), 1)


class TestAlignment(TestCase):

    def test_encode_aligned_int(self):
        sint = Int(1, 'foo', '-72', align='4')
        encoded = sint.encode({}, {}, None)
        self.assertEqual(encoded.int, -72)
        self.assertEqual(encoded.hex, '0xb8')
        self.assertEqual(len(encoded), 4)
        self.assertEqual(encoded._raw, to_bin('0xb800 0000'))

    def test_decode_aligned_int(self):
        sint = Int(1, 'foo', None, align='4')
        decoded = sint.decode(to_bin('0xb800 0000'), None)
        self.assertEqual(decoded.int, -72)
        self.assertEqual(decoded.hex, '0xb8')
        self.assertEqual(len(decoded), 4)
        self.assertEqual(decoded._raw, to_bin('0xb800 0000'))

    def test_encode_aligned_uint(self):
        uint = UInt(1, 'foo', '0xff', align='4')
        encoded = uint.encode({}, {}, None)
        self.assertEqual(encoded.int, 255)
        self.assertEqual(encoded.hex, '0xff')
        self.assertEqual(len(encoded), 4)
        self.assertEqual(encoded._raw, to_bin('0xff00 0000'))

    def test_decode_aligned_uint(self):
        uint = UInt(1, 'foo', None, align='4')
        decoded = uint.decode(to_bin('0xff00 0000'), None)
        self.assertEqual(decoded.int, 255)
        self.assertEqual(decoded.hex, '0xff')
        self.assertEqual(len(decoded), 4)
        self.assertEqual(decoded._raw, to_bin('0xff00 0000'))

    # TODO: more combinations, handling chars


if __name__ == '__main__':
    main()
