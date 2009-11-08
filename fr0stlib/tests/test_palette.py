from unittest import TestCase
import xml.etree.cElementTree as etree
from cStringIO import StringIO
from functools import partial
import colorsys


from fr0stlib import Palette
from fr0stlib import functions



class TestPalette(TestCase):
    def setUp(self):
        self.colorblock = """
        0297C70397C70397C70397C70497C70597C60698C60798C5
        0999C50B99C40C9AC30E9AC3119BC2139CC1159CC0189DBF
        1B9DBE1D9EBC209EBB239FBA269FB929A0B72CA0B62FA0B4
        32A1B336A1B139A1B03CA1AE3FA1AD42A0AB45A0AA48A0A8
        4B9FA64D9FA5509EA3539DA1559DA0589C9E5A9B9D5C9A9B
        5F999A6198986397976595956694936893926A91906B908F
        6C8F8E6E8E8C6F8D8B708C8A718B89728A88728988738987
        748886748786758785758685768685768684768684768584
        768584768584768684768684778685778685778686788786
        7887877988887988887A88897A89897B898A7C898B7D8A8C
        7E8A8C7E8A8D7F8B8E808B8F818C90838C91848D92858D93
        868E94878E95888F968A90988B90998C919A8D919B8F929C
        90939D91949F9394A09495A19596A29796A39898A49A99A5
        9C9AA79D9BA89F9DA9A19EAAA29FABA4A0ACA5A1ADA6A2AD
        A8A3AEA9A4AFAAA5B0ABA6B1ACA7B1ADA7B2AEA8B3AFA9B3
        AFA9B4B0AAB4B1AAB4B1AAB5B1ABB5B2ABB5B2ABB5B2ABB5
        B2ABB5B2ABB5B2ABB5B2ABB5B1AAB5B1AAB5B0A9B4B0A9B4
        AFA8B4AEA7B3ADA6B3ACA5B2ABA4B1A9A3B1A8A2B0A6A1AF
        A59FAFA39EAEA19CAD9F9BAC9C99AB9A98AA9796A99594A8
        9293A79192A68F91A58D91A48B90A38990A28890A18690A0
        84909E82909D80909C7F909B7D909A7B9099799198789197
        7691967592957392947293927092906F918D6E908B6C8F89
        6B8E866A8E84698D82688C80678B7E668B7D658A7B658A79
        648978648977638976638875628874628874628873628873
        628873628873628873618873618873618973618974608974
        608A745F8B745F8B755E8C755D8D765C8E775B8F775A9078
        59917958927A57937B56947C54967D53977F519880509A82
        4E9B844C9D864A9E8848A08A46A18C44A38F42A49240A695
        3DA7973BA99B39AB9E36ACA134AEA531AFA82FB1AC2CB2B0
        29B3B427B2B524B1B622B0B81FAEB91DADBA1BABBC18AABD
        16A8BE14A6BF12A5C010A3C10EA1C20CA0C30B9EC3099DC4
        089CC5079BC5059AC60599C60498C70397C70397C70397C7
        """

        self.xml = """
        <flame>
           <palette count="256" format="RGB">
           %s
           </palette>
        </flame>
        """ % self.colorblock

        self.hex_flame_element = etree.fromstring(self.xml)

        self.data = []
        s = ''.join(self.colorblock.split())

        for idx in range(0, len(s), 6):
            self.data.append(tuple(map(partial(int, base=16), 
                    [s[idx:idx+2], s[idx+2:idx+4], s[idx+4:idx+6]])))

        self.assertEquals(len(self.data), 256)
        
    def check_index(self, palette, index, value):
        self.assertEquals(palette[index, 0], value[0], index)
        self.assertEquals(palette[index, 1], value[1], index)
        self.assertEquals(palette[index, 2], value[2], index)

    def testInit(self):
        palette = Palette()

        for idx in range(256):
            self.check_index(palette, idx, (0, 0, 0))

    def testSequence(self):
        palette = Palette()
        c1 = [1, 2, 3]
        c2 = [1, 2, 4]
        c3 = [1, 2, 5]

        palette[0] = c1
        palette[1] = c2
        palette[2] = c3

        self.check_index(palette, 0, c1)
        self.check_index(palette, 1, c2)
        self.check_index(palette, 2, c3)

    def testFromFlameElement(self):
        palette = Palette.from_flame_element(self.hex_flame_element)

        for idx in range(256):
            self.check_index(palette, idx, self.data[idx])

    def testRotate(self):
        palette = Palette.from_flame_element(self.hex_flame_element)
        palette.rotate(128)

        rotated = self.data[-128:] + self.data[:-128]

        for idx in range(256):
            self.check_index(palette, idx, rotated[idx])

    def testReverse(self):
        palette = Palette.from_flame_element(self.hex_flame_element)
        palette.reverse()

        reversed = self.data[::-1]

        for idx in range(256):
            self.check_index(palette, idx, reversed[idx])

    def testSaturation(self):
        palette = Palette.from_flame_element(self.hex_flame_element)
        palette.saturation(0.5)

        def adjust_saturation(c, v):
            h, l, s = functions.rgb2hls(c)
            return functions.hls2rgb((h, l, s+v))

        adjusted = self.data[:]
        
        for idx, c in enumerate(adjusted):
            adjusted[idx] = adjust_saturation(c, 0.5)

        for idx in range(256):
            self.check_index(palette, idx, adjusted[idx])

    def testFromImage(self):
        palette = Palette()
        palette.from_image(map(ord, image_data), (14, 14))

    def testFromImage(self):
        palette = Palette()
        palette.random()


image_data = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00**xH99\x94s\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x12\x0e\x1f\x1fo0KK\xe0\xb2UU\xea\xd666\xbf\x1c\x00\x00\x00\x00\x00\x00\x00\x00\x0f\x0f-\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\n3\x19FF\xe2\xddFF\xde\xe4QQ\xec\xf4??\xce\xb9;;\xcc8OO\xbc\x87NN\xb2\x8f((Q8\x0f\x0f\x1e!\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01//\xb7 ??\xd1\xa4GG\xe1\xf4UU\xf3\xf7FF\xd8\xc6MM\xdbloo\xf9\xf5xx\xf9\xee\x9b\x9b\xff\xfbnn\xad\x9a\x00\x00\x00\x00\x18\x18]J44\xc0\x9233\xc7r22\xc4\x99::\xcc\x83GG\xdc\xf8MM\xf0\xfaUU\xf0\xfcff\xf7\xfdpp\xf9\xfe\x84\x84\xf9\xfe}}\xf7\xd0**n\x1e\x00\x00\x00\x00\x1f\x1f\x87155\xd0\xd566\xcd\xea==\xd8\xda<<\xcf\xe6CC\xd2\xdcNN\xec\xeeSS\xde\xc7rr\xf9\xfcuu\xfa\xfdff\xef\xf3bb\xed\xd133\xb2\x14\x00\x00\x00\x00\x00\x003\n33\xc7\x9422\xc6\xe0??\xd9\xed@@\xda\xeeAA\xdc\xccFF\xe2\xcb[[\xeb\xdfmm\xf0\xdepp\xf7\xfb[[\xe4\xa5??\xcf0**\xaa\x06\x00\x00\x00\x00\x00\x00\x1e\x11..\xb8t55\xc7\x8e<<\xcc\xacNN\xdc\xe2KK\xda\xa8@@\xe6\xddCC\xe4\xd1GG\xdc\xbeOO\xdc\xdcCC\xd2\xcc;;\xcb\x95**\xb8\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00<<\xce?YY\xe2\xb6\\\\\xe9\xec\\\\\xee\xebUU\xe5\xb2NN\xe3\xbcFF\xd5\xc0GG\xdb\xe8EE\xdb\xf1<<\xd0\x98%%\xbc\x1b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0099\xccPoo\xf2\xf0ii\xf4\xf9[[\xe6\xedQQ\xdf\xdcOO\xe5\xe6JJ\xd7\xd5DD\xd2\xa1>>\xd1\x9777\xd1\x93))\xbeW\x00\x00U\x03\x00\x00\x00\x00\x1b\x1b}ACC\xd1\xcbff\xe7\xdbjj\xf3\xf7ZZ\xe3\xa0SS\xdf\xd0WW\xee\xf5NN\xde\xdfCC\xd0W\x17\x17\xa2\x0b\x00\x00f\x05""\xad\x16\x00\x00\x00\x00\x00\x00\x00\x00\x15\x15c;&&\xa3j++\xc3cHH\xd6\xa5FF\xd46AA\xd2\x8f]]\xf0\xf4EE\xd8\xc533\xc9i\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1b\x1b\x91\x1c**\xb4\x18\x00\x00\x00\x00\x1f\x1f\xbf\x10==\xcf\xb7++\xc1S))\xbd\x1f\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\x07((\xc3p%%\xc3"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

