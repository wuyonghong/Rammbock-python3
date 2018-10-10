from unittest import TestCase, main
from Rammbock.message import Struct, Field, BinaryContainer, BinaryField
from Rammbock.binary_tools import to_bin


def uint_field(value='0x00'):
    return Field('uint', 'name', to_bin(value))


class TestMessages(TestCase):

    def test_in(self):
        msg = Struct('foo', 'foo_type')
        msg['a'] = uint_field()
        msg['b'] = uint_field()
        msg['c'] = uint_field()
        self.assertTrue('a' in msg)
        self.assertFalse('d' in msg)

    def test_parent_references(self):
        msg = Struct('foo', 'foo_type')
        child = Struct('sub', 'subelement_type')
        child['field'] = uint_field()
        msg['subbi'] = child
        self.assertEqual(msg, child._parent)
        self.assertEqual(msg, child['field']._parent._parent)

    def test_conversions(self):
        field = Field('unit', 'name', to_bin('0x00616200'))
        self.assertEqual(field.int, 0x00616200)
        self.assertEqual(field.hex, '0x00616200')
        self.assertEqual(field.ascii, 'ab')
        self.assertEqual(field.bytes, b'\x00\x61\x62\x00')
        self.assertEqual(field.chars, 'ab')
        self.assertEqual(field.bin, '0b00000000' + '01100001' + '01100010' + '00000000')

    def test_not_iterable(self):
        msg = Struct('foo', 'foo_type')
        msg['a'] = uint_field()
        self.assertRaises(TypeError, iter, msg)
        self.assertRaises(TypeError, iter, msg.a)


class TestBinaryContainer(TestCase):

    def _bin_container(self, little_endian=False):
        cont = BinaryContainer('foo', little_endian=little_endian)
        cont['three'] = BinaryField(3, 'three', to_bin('0b101'))
        cont['six'] = BinaryField(6, 'six', to_bin('0b101010'))
        cont['seven'] = BinaryField(7, 'seven', to_bin('0b0101010'))
        return cont

    def setUp(self):
        self.cont = self._bin_container()

    def test_create_binary_container(self):
        self.assertEqual(self.cont.three.bin, '0b101')
        self.assertEqual(self.cont.six.bin, '0b101010')
        self.assertEqual(self.cont.seven.bin, '0b0101010')

    def test_conversions(self):
        self.assertEqual(self.cont.seven.int, 42)
        self.assertEqual(self.cont.seven.bytes, to_bin(42))
        self.assertEqual(self.cont.seven.ascii, '*')

    def test_get_binary_container_bytes(self):
        self.assertEqual(self.cont._raw, to_bin('0b1011 0101 0010 1010'))

    def test_binary_container_length(self):
        self.assertEqual(int(self.cont.__len__()), 2)

    def test_little_endian_bin_container(self):
        little = self._bin_container(little_endian=True)
        self.assertEqual(little.three.bin, '0b101')
        self.assertEqual(little.six.bin, '0b101010')
        self.assertEqual(little.seven.bin, '0b0101010')
        self.assertEqual(little._raw, to_bin('0b0010 1010 1011 0101'))

    def test_pretty_print_container(self):
        expected = '''BinaryContainer foo
  three = 0b101 (0x05)
  six = 0b101010 (0x2a)
  seven = 0b0101010 (0x2a)
'''
        self.assertEqual(repr(self._bin_container()), expected)
        self.assertEqual(repr(self._bin_container(little_endian=True)), expected)


class TestFieldAlignment(TestCase):

    def _assert_align(self, value, length, raw):
        field = Field('uint', 'name', to_bin(value), aligned_len=length)
        self.assertEqual(field.int, int(value, 16))
        self.assertEqual(field.hex, value)
        self.assertEqual(field._raw, to_bin(raw))
        self.assertEqual(field.bytes, to_bin(value))
        if length:
            self.assertEqual(int(field.__len__()), length)

    def test_align_field(self):
        self._assert_align('0xff', 4, '0xff00 0000')
        self._assert_align('0x00ff', 4, '0x00ff 0000')
        self._assert_align('0x00', 4, '0x0000 0000')
        self._assert_align('0xff', None, '0xff')
        self._assert_align('0xff', 6, '0xff00 0000 0000')
        self._assert_align('0x000000ff', 4, '0x0000 00ff')
        self._assert_align('0xff', 1, '0xff')


class TestLittleEndian(TestCase):

    def test_little_endian(self):
        field = Field('uint', 'name', to_bin('0x0100'), little_endian=True)
        self.assertEqual(field._raw, to_bin('0x0100'))
        self.assertEqual(field.int, 1)
        self.assertEqual(field.bytes, to_bin('0x0001'))
        self.assertEqual(field.hex, '0x0001')

    def test_little_endian_with_align(self):
        field = Field('uint', 'name', to_bin('0x0100'), aligned_len=5, little_endian=True)
        self.assertEqual(field._raw, to_bin('0x0100000000'))
        self.assertEqual(field.int, 1)
        self.assertEqual(field.bytes, to_bin('0x0001'))
        self.assertEqual(field.hex, '0x0001')


if __name__ == "__main__":
    main()
