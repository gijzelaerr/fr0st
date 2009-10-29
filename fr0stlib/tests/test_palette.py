from unittest import TestCase
import xml.etree.cElementTree as etree
from cStringIO import StringIO
from functools import partial


from fr0stlib import Palette2 as Palette



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

    def testFromString(self):
        palette = Palette.from_string(self.xml)

        for idx in range(256):
            self.check_index(palette, idx, self.data[idx])

    def testFromFlameElement(self):
        sfd = StringIO(self.xml)
        tree = etree.parse(sfd)

        self.assertEquals(tree.getroot().tag, 'flame')

        palette = Palette.from_flame_element(tree.getroot())

        for idx in range(256):
            self.check_index(palette, idx, self.data[idx])

    def testRotate(self):
        palette = Palette.from_string(self.xml)
        palette.rotate(128)

        rotated = self.data[-128:] + self.data[:-128]

        for idx in range(256):
            self.check_index(palette, idx, rotated[idx])



