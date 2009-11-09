##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################
from unittest import TestCase
import xml.etree.ElementTree
import xml.etree.cElementTree as etree
import operator
from fr0stlib import Chaos, Flame, Xform, PostXform
from fr0stlib.pyflam3.variations import variation_list


flame_str = """
<flame name="Untitled" size="512 384" center="0 0" scale="128.0" rotate="0" brightness="4" background="0 0 0" version="fr0st 0.5 alpha" gamma_threshold="0.04" highlight_power="-1" gamma="4" >
   <xform linear="1.0" weight="1.0" color="0.0" coefs="1.0 -0.0 -0.0 1.0 0.0 -0.0" chaos="1.0 1.0 1.0 0.0 " />
   <xform linear="1" weight="1" color="0" coefs="1.0 -0.0 -0.0 1.0 0.0 -0.0" chaos="1.0 0.0 0.0 0.0 " />
   <xform linear="1" weight="1" color="0" coefs="1.0 -0.0 -0.0 1.0 0.0 -0.0" chaos="1.0 0.0 0.0 0.0 " />
   <xform linear="1" weight="1" color="0" coefs="1.0 -0.0 -0.0 1.0 0.0 -0.0" chaos="1.0 0.0 0.0 " />
   <finalxform linear="1" color="0" color_speed="0" coefs="1.0 -0.0 -0.0 1.0 0.0 -0.0" />
   <color index="0" rgb="128 211 253"/>
   <color index="1" rgb="128 211 253"/>
   <color index="2" rgb="128 211 253"/>
   <color index="3" rgb="128 211 253"/>
   <color index="4" rgb="128 211 253"/>
   <color index="5" rgb="128 211 253"/>
   <color index="6" rgb="128 211 253"/>
   <color index="7" rgb="128 211 253"/>
   <color index="8" rgb="128 211 253"/>
   <color index="9" rgb="128 211 252"/>
   <color index="10" rgb="128 211 252"/>
   <color index="11" rgb="128 211 252"/>
   <color index="12" rgb="128 211 251"/>
   <color index="13" rgb="128 210 251"/>
   <color index="14" rgb="128 210 251"/>
   <color index="15" rgb="128 210 250"/>
   <color index="16" rgb="128 210 250"/>
   <color index="17" rgb="128 210 249"/>
   <color index="18" rgb="128 210 249"/>
   <color index="19" rgb="128 210 249"/>
   <color index="20" rgb="128 210 248"/>
   <color index="21" rgb="127 210 247"/>
   <color index="22" rgb="127 210 247"/>
   <color index="23" rgb="127 210 246"/>
   <color index="24" rgb="127 209 246"/>
   <color index="25" rgb="127 209 245"/>
   <color index="26" rgb="127 209 244"/>
   <color index="27" rgb="127 209 244"/>
   <color index="28" rgb="127 209 243"/>
   <color index="29" rgb="127 209 242"/>
   <color index="30" rgb="127 209 241"/>
   <color index="31" rgb="127 208 241"/>
   <color index="32" rgb="127 208 240"/>
   <color index="33" rgb="127 208 239"/>
   <color index="34" rgb="127 208 238"/>
   <color index="35" rgb="127 207 237"/>
   <color index="36" rgb="126 207 237"/>
   <color index="37" rgb="126 207 236"/>
   <color index="38" rgb="126 207 235"/>
   <color index="39" rgb="126 206 234"/>
   <color index="40" rgb="126 206 233"/>
   <color index="41" rgb="126 206 232"/>
   <color index="42" rgb="126 206 231"/>
   <color index="43" rgb="126 205 230"/>
   <color index="44" rgb="125 205 229"/>
   <color index="45" rgb="125 205 228"/>
   <color index="46" rgb="125 204 227"/>
   <color index="47" rgb="125 204 226"/>
   <color index="48" rgb="125 203 225"/>
   <color index="49" rgb="125 203 224"/>
   <color index="50" rgb="124 203 223"/>
   <color index="51" rgb="124 202 222"/>
   <color index="52" rgb="124 202 221"/>
   <color index="53" rgb="124 201 220"/>
   <color index="54" rgb="124 201 218"/>
   <color index="55" rgb="123 200 217"/>
   <color index="56" rgb="123 200 216"/>
   <color index="57" rgb="123 199 215"/>
   <color index="58" rgb="123 199 214"/>
   <color index="59" rgb="123 198 213"/>
   <color index="60" rgb="122 198 212"/>
   <color index="61" rgb="122 197 211"/>
   <color index="62" rgb="122 197 210"/>
   <color index="63" rgb="122 196 208"/>
   <color index="64" rgb="121 195 207"/>
   <color index="65" rgb="121 195 206"/>
   <color index="66" rgb="121 194 205"/>
   <color index="67" rgb="121 194 204"/>
   <color index="68" rgb="120 193 203"/>
   <color index="69" rgb="120 192 202"/>
   <color index="70" rgb="120 192 200"/>
   <color index="71" rgb="120 191 199"/>
   <color index="72" rgb="119 190 198"/>
   <color index="73" rgb="119 190 197"/>
   <color index="74" rgb="119 189 196"/>
   <color index="75" rgb="118 188 195"/>
   <color index="76" rgb="118 188 194"/>
   <color index="77" rgb="118 187 193"/>
   <color index="78" rgb="118 186 192"/>
   <color index="79" rgb="117 186 191"/>
   <color index="80" rgb="117 185 190"/>
   <color index="81" rgb="117 184 189"/>
   <color index="82" rgb="116 184 187"/>
   <color index="83" rgb="116 183 186"/>
   <color index="84" rgb="116 182 185"/>
   <color index="85" rgb="115 182 184"/>
   <color index="86" rgb="115 181 183"/>
   <color index="87" rgb="115 180 183"/>
   <color index="88" rgb="115 180 182"/>
   <color index="89" rgb="114 179 181"/>
   <color index="90" rgb="114 179 180"/>
   <color index="91" rgb="114 178 179"/>
   <color index="92" rgb="113 177 178"/>
   <color index="93" rgb="113 177 177"/>
   <color index="94" rgb="113 176 176"/>
   <color index="95" rgb="113 175 175"/>
   <color index="96" rgb="112 175 174"/>
   <color index="97" rgb="112 174 173"/>
   <color index="98" rgb="112 173 172"/>
   <color index="99" rgb="112 172 171"/>
   <color index="100" rgb="111 172 170"/>
   <color index="101" rgb="111 171 170"/>
   <color index="102" rgb="111 170 169"/>
   <color index="103" rgb="111 169 168"/>
   <color index="104" rgb="110 169 167"/>
   <color index="105" rgb="110 168 166"/>
   <color index="106" rgb="110 168 166"/>
   <color index="107" rgb="110 167 165"/>
   <color index="108" rgb="109 166 164"/>
   <color index="109" rgb="109 166 164"/>
   <color index="110" rgb="109 165 163"/>
   <color index="111" rgb="109 165 162"/>
   <color index="112" rgb="109 165 162"/>
   <color index="113" rgb="109 164 161"/>
   <color index="114" rgb="108 164 161"/>
   <color index="115" rgb="108 163 160"/>
   <color index="116" rgb="108 163 160"/>
   <color index="117" rgb="108 163 160"/>
   <color index="118" rgb="108 162 159"/>
   <color index="119" rgb="108 162 159"/>
   <color index="120" rgb="108 162 159"/>
   <color index="121" rgb="108 162 158"/>
   <color index="122" rgb="108 162 158"/>
   <color index="123" rgb="108 161 158"/>
   <color index="124" rgb="108 161 158"/>
   <color index="125" rgb="107 161 158"/>
   <color index="126" rgb="107 161 158"/>
   <color index="127" rgb="107 161 158"/>
   <color index="128" rgb="107 161 158"/>
   <color index="129" rgb="107 161 158"/>
   <color index="130" rgb="107 161 158"/>
   <color index="131" rgb="107 161 158"/>
   <color index="132" rgb="108 161 158"/>
   <color index="133" rgb="108 161 158"/>
   <color index="134" rgb="108 162 158"/>
   <color index="135" rgb="108 162 158"/>
   <color index="136" rgb="108 162 159"/>
   <color index="137" rgb="108 162 159"/>
   <color index="138" rgb="108 162 159"/>
   <color index="139" rgb="108 163 160"/>
   <color index="140" rgb="108 163 160"/>
   <color index="141" rgb="108 163 160"/>
   <color index="142" rgb="108 164 161"/>
   <color index="143" rgb="109 164 161"/>
   <color index="144" rgb="109 165 162"/>
   <color index="145" rgb="109 165 162"/>
   <color index="146" rgb="109 165 163"/>
   <color index="147" rgb="109 166 164"/>
   <color index="148" rgb="109 166 164"/>
   <color index="149" rgb="110 167 165"/>
   <color index="150" rgb="110 168 166"/>
   <color index="151" rgb="110 168 166"/>
   <color index="152" rgb="110 169 167"/>
   <color index="153" rgb="111 169 168"/>
   <color index="154" rgb="111 170 169"/>
   <color index="155" rgb="111 171 170"/>
   <color index="156" rgb="111 172 170"/>
   <color index="157" rgb="112 172 171"/>
   <color index="158" rgb="112 173 172"/>
   <color index="159" rgb="112 174 173"/>
   <color index="160" rgb="112 175 174"/>
   <color index="161" rgb="113 175 175"/>
   <color index="162" rgb="113 176 176"/>
   <color index="163" rgb="113 177 177"/>
   <color index="164" rgb="113 177 178"/>
   <color index="165" rgb="114 178 179"/>
   <color index="166" rgb="114 179 180"/>
   <color index="167" rgb="114 179 181"/>
   <color index="168" rgb="115 180 182"/>
   <color index="169" rgb="115 180 183"/>
   <color index="170" rgb="115 181 183"/>
   <color index="171" rgb="115 182 184"/>
   <color index="172" rgb="116 182 185"/>
   <color index="173" rgb="116 183 186"/>
   <color index="174" rgb="116 184 187"/>
   <color index="175" rgb="117 184 189"/>
   <color index="176" rgb="117 185 190"/>
   <color index="177" rgb="117 186 191"/>
   <color index="178" rgb="118 186 192"/>
   <color index="179" rgb="118 187 193"/>
   <color index="180" rgb="118 188 194"/>
   <color index="181" rgb="118 188 195"/>
   <color index="182" rgb="119 189 196"/>
   <color index="183" rgb="119 190 197"/>
   <color index="184" rgb="119 190 198"/>
   <color index="185" rgb="120 191 199"/>
   <color index="186" rgb="120 192 200"/>
   <color index="187" rgb="120 192 202"/>
   <color index="188" rgb="120 193 203"/>
   <color index="189" rgb="121 194 204"/>
   <color index="190" rgb="121 194 205"/>
   <color index="191" rgb="121 195 206"/>
   <color index="192" rgb="121 195 207"/>
   <color index="193" rgb="122 196 208"/>
   <color index="194" rgb="122 197 210"/>
   <color index="195" rgb="122 197 211"/>
   <color index="196" rgb="122 198 212"/>
   <color index="197" rgb="123 198 213"/>
   <color index="198" rgb="123 199 214"/>
   <color index="199" rgb="123 199 215"/>
   <color index="200" rgb="123 200 216"/>
   <color index="201" rgb="123 200 217"/>
   <color index="202" rgb="124 201 218"/>
   <color index="203" rgb="124 201 220"/>
   <color index="204" rgb="124 202 221"/>
   <color index="205" rgb="124 202 222"/>
   <color index="206" rgb="124 203 223"/>
   <color index="207" rgb="125 203 224"/>
   <color index="208" rgb="125 203 225"/>
   <color index="209" rgb="125 204 226"/>
   <color index="210" rgb="125 204 227"/>
   <color index="211" rgb="125 205 228"/>
   <color index="212" rgb="125 205 229"/>
   <color index="213" rgb="126 205 230"/>
   <color index="214" rgb="126 206 231"/>
   <color index="215" rgb="126 206 232"/>
   <color index="216" rgb="126 206 233"/>
   <color index="217" rgb="126 206 234"/>
   <color index="218" rgb="126 207 235"/>
   <color index="219" rgb="126 207 236"/>
   <color index="220" rgb="126 207 237"/>
   <color index="221" rgb="127 207 237"/>
   <color index="222" rgb="127 208 238"/>
   <color index="223" rgb="127 208 239"/>
   <color index="224" rgb="127 208 240"/>
   <color index="225" rgb="127 208 241"/>
   <color index="226" rgb="127 209 241"/>
   <color index="227" rgb="127 209 242"/>
   <color index="228" rgb="127 209 243"/>
   <color index="229" rgb="127 209 244"/>
   <color index="230" rgb="127 209 244"/>
   <color index="231" rgb="127 209 245"/>
   <color index="232" rgb="127 209 246"/>
   <color index="233" rgb="127 210 246"/>
   <color index="234" rgb="127 210 247"/>
   <color index="235" rgb="127 210 247"/>
   <color index="236" rgb="128 210 248"/>
   <color index="237" rgb="128 210 249"/>
   <color index="238" rgb="128 210 249"/>
   <color index="239" rgb="128 210 249"/>
   <color index="240" rgb="128 210 250"/>
   <color index="241" rgb="128 210 250"/>
   <color index="242" rgb="128 210 251"/>
   <color index="243" rgb="128 210 251"/>
   <color index="244" rgb="128 211 251"/>
   <color index="245" rgb="128 211 252"/>
   <color index="246" rgb="128 211 252"/>
   <color index="247" rgb="128 211 252"/>
   <color index="248" rgb="128 211 253"/>
   <color index="249" rgb="128 211 253"/>
   <color index="250" rgb="128 211 253"/>
   <color index="251" rgb="128 211 253"/>
   <color index="252" rgb="128 211 253"/>
   <color index="253" rgb="128 211 253"/>
   <color index="254" rgb="128 211 253"/>
   <color index="255" rgb="128 211 253"/>
</flame>
"""

class TestXform(TestCase):
    def setUp(self):
        self.flame = Flame(flame_str)

    def assertTupleAlmostEquals(self, a, b):
        for received, expected in zip(a, b):
            self.assertAlmostEquals(received, expected, 7, "%s != %s" % (a, b))

    def test_tostring(self):
        s = self.flame.xform[0].to_string()
        e = etree.fromstring(s)
    
        self.assertEquals(e.tag, 'xform')
        self.assertEquals(float(e.attrib['linear']), 1.0)
        self.assertEquals(float(e.attrib['weight']), 1.0)
        self.assertEquals(float(e.attrib['color']), 0.0)
        self.assertEquals(map(float, e.attrib['coefs'].split()), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(map(float, e.attrib['chaos'].split()), [1.0, 1.0, 1.0, 0.0])

        attrib_keys = e.attrib.keys()
        attrib_keys.remove('linear')
        attrib_keys.remove('weight')
        attrib_keys.remove('color')
        attrib_keys.remove('coefs')
        attrib_keys.remove('chaos')
        self.assertEquals(attrib_keys, [])

    def test_repr(self):
        self.assertEquals(repr(self.flame.xform[0]), '<xform 1>')
        self.assertEquals(repr(self.flame.xform[1]), '<xform 2>')
        self.assertEquals(repr(self.flame.xform[2]), '<xform 3>')
        self.assertEquals(repr(self.flame.xform[3]), '<xform 4>')

    def test_getattr(self):
        x = self.flame.xform[0]

        for var in variation_list:
            if var == 'linear':
                self.assertEquals(getattr(x, var), 1.0)
            else:
                self.assertEquals(getattr(x, var), 0.0)

        self.assertRaises(AttributeError, lambda: getattr(x, '__setstate__'))

    def test_chaos(self):
        x = self.flame.xform[0]
        self.assertEquals(x.chaos[:], [1.0, 1.0, 1.0, 0.0])

    def test_post(self):
        x = self.flame.xform[0]
        self.assertEquals(list(x.post.coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])

        self.assertRaises(TypeError, lambda: setattr(x, 'post', 1))

        orig = x.post
        p = PostXform(x, coefs=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        x.post = p

        self.assertEquals(list(x.post.coefs), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        x.post = orig
        self.assertEquals(list(x.post.coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])

    def test_index(self):
        self.assertEquals(self.flame.xform[0].index, 0)
        self.assertEquals(self.flame.xform[1].index, 1)
        self.assertEquals(self.flame.xform[2].index, 2)
        self.assertEquals(self.flame.xform[3].index, 3)
        self.assertEquals(self.flame.final.index, None)

    def test_coefs(self):
        self.assertEquals(list(self.flame.xform[0].coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.xform[1].coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.xform[2].coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.xform[3].coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.final.coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])

        self.assertEquals(list(self.flame.xform[0].screen_coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.xform[1].screen_coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.xform[2].screen_coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.xform[3].screen_coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEquals(list(self.flame.final.screen_coefs), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])

    def test_list_variations(self):
        self.assertEquals(self.flame.xform[0].list_variations(), ['linear'])
        self.assertEquals(self.flame.xform[1].list_variations(), ['linear'])
        self.assertEquals(self.flame.xform[2].list_variations(), ['linear'])
        self.assertEquals(self.flame.xform[3].list_variations(), ['linear'])
        self.assertEquals(self.flame.final.list_variations(), ['linear'])

        
    def test_iter_attributes(self):
        def test_func(x, is_final=False):
            attr = { 'linear': 1.0, 'weight': 1.0, 'color': 0.0 }

            if is_final:
                del attr['weight']
                attr['color_speed'] = 0.0

            xattr = dict(x.iter_attributes())

            self.assertEquals(xattr, attr)

        test_func(self.flame.xform[0])
        test_func(self.flame.xform[1])
        test_func(self.flame.xform[2])
        test_func(self.flame.xform[3])
        test_func(self.flame.final, True)

    def test_pos(self):
        self.assertEquals(self.flame.xform[0].pos, (0.0, 0.0))
        self.assertEquals(self.flame.xform[1].pos, (0.0, 0.0))
        self.assertEquals(self.flame.xform[2].pos, (0.0, 0.0))
        self.assertEquals(self.flame.xform[3].pos, (0.0, 0.0))
        self.assertEquals(self.flame.final.pos, (0.0, 0.0))

        self.flame.xform[0].pos = (1.0, 2.0)
        self.flame.xform[1].pos = (3.0, 4.0)
        self.flame.xform[2].pos = (5.0, 6.0)
        self.flame.xform[3].pos = (7.0, 8.0)
        self.flame.final.pos = (9.0, 10.0)

        self.assertEquals(self.flame.xform[0].pos, (1.0, 2.0))
        self.assertEquals(self.flame.xform[1].pos, (3.0, 4.0))
        self.assertEquals(self.flame.xform[2].pos, (5.0, 6.0))
        self.assertEquals(self.flame.xform[3].pos, (7.0, 8.0))
        self.assertEquals(self.flame.final.pos, (9.0, 10.0))

        self.flame.xform[0].move_pos(-1.0, -2.0)
        self.flame.xform[1].move_pos(-3.0, -4.0)
        self.flame.xform[2].move_pos(-5.0, -6.0)
        self.flame.xform[3].move_pos(-7.0, -8.0)
        self.flame.final.move_pos(-9.0, -10.0)

        self.assertEquals(self.flame.xform[0].pos, (0.0, 0.0))
        self.assertEquals(self.flame.xform[1].pos, (0.0, 0.0))
        self.assertEquals(self.flame.xform[2].pos, (0.0, 0.0))
        self.assertEquals(self.flame.xform[3].pos, (0.0, 0.0))
        self.assertEquals(self.flame.final.pos, (0.0, 0.0))

    def test_x(self):
        self.assertEquals(self.flame.xform[0].x, (1.0, 0.0))
        self.assertEquals(self.flame.xform[1].x, (1.0, 0.0))
        self.assertEquals(self.flame.xform[2].x, (1.0, 0.0))
        self.assertEquals(self.flame.xform[3].x, (1.0, 0.0))
        self.assertEquals(self.flame.final.x, (1.0, 0.0))

        self.flame.xform[0].x = (1.0, 2.0)
        self.flame.xform[1].x = (3.0, 4.0)
        self.flame.xform[2].x = (5.0, 6.0)
        self.flame.xform[3].x = (7.0, 8.0)
        self.flame.final.x = (9.0, 10.0)

        self.assertEquals(self.flame.xform[0].x, (1.0, 2.0))
        self.assertEquals(self.flame.xform[1].x, (3.0, 4.0))
        self.assertEquals(self.flame.xform[2].x, (5.0, 6.0))
        self.assertEquals(self.flame.xform[3].x, (7.0, 8.0))
        self.assertEquals(self.flame.final.x, (9.0, 10.0))

        self.flame.xform[0].move_x( 0.0, -2.0)
        self.flame.xform[1].move_x(-2.0, -4.0)
        self.flame.xform[2].move_x(-4.0, -6.0)
        self.flame.xform[3].move_x(-6.0, -8.0)
        self.flame.final.move_x(-8.0, -10.0)

        self.assertEquals(self.flame.xform[0].x, (1.0, 0.0))
        self.assertEquals(self.flame.xform[1].x, (1.0, 0.0))
        self.assertEquals(self.flame.xform[2].x, (1.0, 0.0))
        self.assertEquals(self.flame.xform[3].x, (1.0, 0.0))
        self.assertEquals(self.flame.final.x, (1.0, 0.0))

    def test_y(self):
        self.assertEquals(self.flame.xform[0].y, (0.0, 1.0))
        self.assertEquals(self.flame.xform[1].y, (0.0, 1.0))
        self.assertEquals(self.flame.xform[2].y, (0.0, 1.0))
        self.assertEquals(self.flame.xform[3].y, (0.0, 1.0))
        self.assertEquals(self.flame.final.y, (0.0, 1.0))

        self.flame.xform[0].y = (1.0, 2.0)
        self.flame.xform[1].y = (3.0, 4.0)
        self.flame.xform[2].y = (5.0, 6.0)
        self.flame.xform[3].y = (7.0, 8.0)
        self.flame.final.y = (9.0, 10.0)

        self.assertEquals(self.flame.xform[0].y, (1.0, 2.0))
        self.assertEquals(self.flame.xform[1].y, (3.0, 4.0))
        self.assertEquals(self.flame.xform[2].y, (5.0, 6.0))
        self.assertEquals(self.flame.xform[3].y, (7.0, 8.0))
        self.assertEquals(self.flame.final.y, (9.0, 10.0))

        self.flame.xform[0].move_y(-1.0, -1.0)
        self.flame.xform[1].move_y(-3.0, -3.0)
        self.flame.xform[2].move_y(-5.0, -5.0)
        self.flame.xform[3].move_y(-7.0, -7.0)
        self.flame.final.move_y(-9.0, -9.0)

        self.assertEquals(self.flame.xform[0].y, (0.0, 1.0))
        self.assertEquals(self.flame.xform[1].y, (0.0, 1.0))
        self.assertEquals(self.flame.xform[2].y, (0.0, 1.0))
        self.assertEquals(self.flame.xform[3].y, (0.0, 1.0))
        self.assertEquals(self.flame.final.y, (0.0, 1.0))

    def test_o(self):
        self.assertEquals(self.flame.xform[0].o, (0.0, 0.0))
        self.assertEquals(self.flame.xform[1].o, (0.0, 0.0))
        self.assertEquals(self.flame.xform[2].o, (0.0, 0.0))
        self.assertEquals(self.flame.xform[3].o, (0.0, 0.0))
        self.assertEquals(self.flame.final.o, (0.0, 0.0))

        self.flame.xform[0].o = (1.0, 2.0)
        self.flame.xform[1].o = (3.0, 4.0)
        self.flame.xform[2].o = (5.0, 6.0)
        self.flame.xform[3].o = (7.0, 8.0)
        self.flame.final.o = (9.0, 10.0)

        self.assertEquals(self.flame.xform[0].o, (1.0, 2.0))
        self.assertEquals(self.flame.xform[1].o, (3.0, 4.0))
        self.assertEquals(self.flame.xform[2].o, (5.0, 6.0))
        self.assertEquals(self.flame.xform[3].o, (7.0, 8.0))
        self.assertEquals(self.flame.final.o, (9.0, 10.0))

        self.flame.xform[0].move_o(-1.0, -2.0)
        self.flame.xform[1].move_o(-3.0, -4.0)
        self.flame.xform[2].move_o(-5.0, -6.0)
        self.flame.xform[3].move_o(-7.0, -8.0)
        self.flame.final.move_o(-9.0, -10.0)

        self.assertEquals(self.flame.xform[0].o, (0.0, 0.0))
        self.assertEquals(self.flame.xform[1].o, (0.0, 0.0))
        self.assertEquals(self.flame.xform[2].o, (0.0, 0.0))
        self.assertEquals(self.flame.xform[3].o, (0.0, 0.0))
        self.assertEquals(self.flame.final.o, (0.0, 0.0))

    def test_points(self):
        self.assertEquals(self.flame.xform[0].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)))
        self.assertEquals(self.flame.xform[1].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))) 
        self.assertEquals(self.flame.xform[2].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))) 
        self.assertEquals(self.flame.xform[3].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))) 
        self.assertEquals(self.flame.final.points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))) 

        self.flame.xform[0].points = ((1.0, 2.0), (3.0, 4.0), (5.0, 6.0))
        self.flame.xform[1].points = ((3.0, 4.0), (5.0, 6.0), (7.0, 8.0))
        self.flame.xform[2].points = ((5.0, 6.0), (7.0, 8.0), (9.0, 10.0))
        self.flame.xform[3].points = ((7.0, 8.0), (9.0, 10.0), (11.0, 12.0))
        self.flame.final.points =    ((9.0, 10.0), (11.0, 12.0), (13.0, 14.0))

        self.assertEquals(self.flame.xform[0].points, ((1.0, 2.0), (3.0, 4.0), (5.0, 6.0)))
        self.assertEquals(self.flame.xform[1].points, ((3.0, 4.0), (5.0, 6.0), (7.0, 8.0)))
        self.assertEquals(self.flame.xform[2].points, ((5.0, 6.0), (7.0, 8.0), (9.0, 10.0)))
        self.assertEquals(self.flame.xform[3].points, ((7.0, 8.0), (9.0, 10.0), (11.0, 12.0)))
        self.assertEquals(self.flame.final.points,    ((9.0, 10.0), (11.0, 12.0), (13.0, 14.0)))

        self.flame.xform[0].points = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
        self.flame.xform[1].points = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
        self.flame.xform[2].points = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
        self.flame.xform[3].points = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
        self.flame.final.points =    ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))

        self.assertEquals(self.flame.xform[0].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)))
        self.assertEquals(self.flame.xform[1].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)))
        self.assertEquals(self.flame.xform[2].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)))
        self.assertEquals(self.flame.xform[3].points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)))
        self.assertEquals(self.flame.final.points, ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)))

    def test_polar(self):
        self.assertEquals(self.flame.xform[0].xp, (1, 0))
        self.assertEquals(self.flame.xform[1].xp, (1, 0))
        self.assertEquals(self.flame.xform[2].xp, (1, 0))
        self.assertEquals(self.flame.xform[3].xp, (1, 0))
        self.assertEquals(self.flame.final.xp, (1, 0))

        self.assertEquals(self.flame.xform[0].yp, (1, 90))
        self.assertEquals(self.flame.xform[1].yp, (1, 90))
        self.assertEquals(self.flame.xform[2].yp, (1, 90))
        self.assertEquals(self.flame.xform[3].yp, (1, 90))
        self.assertEquals(self.flame.final.yp, (1, 90))

        self.assertEquals(self.flame.xform[0].op, (0, 0))
        self.assertEquals(self.flame.xform[1].op, (0, 0))
        self.assertEquals(self.flame.xform[2].op, (0, 0))
        self.assertEquals(self.flame.xform[3].op, (0, 0))
        self.assertEquals(self.flame.final.op, (0, 0))

        self.assertEquals(self.flame.xform[0].polars, ((1, 0), (1, 90), (0, 0)))
        self.assertEquals(self.flame.xform[1].polars, ((1, 0), (1, 90), (0, 0)))
        self.assertEquals(self.flame.xform[2].polars, ((1, 0), (1, 90), (0, 0)))
        self.assertEquals(self.flame.xform[3].polars, ((1, 0), (1, 90), (0, 0)))
        self.assertEquals(self.flame.final.polars,    ((1, 0), (1, 90), (0, 0)))

        self.flame.xform[0].xp = (1.0, 180.0)
        self.assertTupleAlmostEquals(self.flame.xform[0].x, (-1, 0))

        self.flame.xform[0].xp = (1.0, 270.0)
        self.assertTupleAlmostEquals(self.flame.xform[0].x, (0, -1))

        self.flame.xform[0].xp = (1.0, 360)
        self.assertTupleAlmostEquals(self.flame.xform[0].x, (1, 0))

    def test_scale(self):
        x = self.flame.xform[0]

        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.scale_x(0.5)
        self.assertTupleAlmostEquals(x.x, (0.5, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.scale_x(2)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.scale_y(0.5)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 0.5))

        x.scale_y(2)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.scale(0.5)
        self.assertTupleAlmostEquals(x.x, (0.5, 0))
        self.assertTupleAlmostEquals(x.y, (0, 0.5))

        x.scale(2)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

    def test_rotate(self):
        x = self.flame.xform[0]

        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.rotate_x(90)
        self.assertTupleAlmostEquals(x.x, (0, 1))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.rotate_x(-90)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.rotate_y(180)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, -1))

        x.rotate_y(-180)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

        x.rotate(270)
        self.assertTupleAlmostEquals(x.x, (0, -1))
        self.assertTupleAlmostEquals(x.y, (1,  0))

        x.rotate(-270)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))

    def test_move(self):
        x = self.flame.xform[0]

        x.move(1)
        self.assertTupleAlmostEquals(x.x, (2, 0))
        self.assertTupleAlmostEquals(x.y, (1, 1))
        self.assertTupleAlmostEquals(x.o, (1, 0))

        x.move(-1)
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))
        self.assertTupleAlmostEquals(x.o, (0, 0))

    def test_orbit(self):
        x = self.flame.xform[0]

        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))
        self.assertTupleAlmostEquals(x.o, (0, 0))

        x.move_x((1, 1))
        x.move_y((1, 1))
        x.move_o((1, 1))
        self.assertTupleAlmostEquals(x.x, (2, 1))
        self.assertTupleAlmostEquals(x.y, (1, 2))
        self.assertTupleAlmostEquals(x.o, (1, 1))

        x.orbit(90)
        self.assertTupleAlmostEquals(x.x, (0, 1))
        self.assertTupleAlmostEquals(x.y, (-1, 2))
        self.assertTupleAlmostEquals(x.o, (-1, 1))

        x.orbit(-90)
        self.assertTupleAlmostEquals(x.x, (2, 1))
        self.assertTupleAlmostEquals(x.y, (1, 2))
        self.assertTupleAlmostEquals(x.o, (1, 1))

        x.move_x((-1, -1))
        x.move_y((-1, -1))
        x.move_o((-1, -1))

        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))
        self.assertTupleAlmostEquals(x.o, (0, 0))

        x.orbit(90, pivot=(1,1))
        self.assertTupleAlmostEquals(x.x, (3, 0))
        self.assertTupleAlmostEquals(x.y, (2, 1))
        self.assertTupleAlmostEquals(x.o, (2, 0))

        x.orbit(-90, pivot=(1,1))
        self.assertTupleAlmostEquals(x.x, (1, 0))
        self.assertTupleAlmostEquals(x.y, (0, 1))
        self.assertTupleAlmostEquals(x.o, (0, 0))

    def test_ispost(self):
        self.assertEquals(self.flame.xform[0].ispost(), False)
        self.assertEquals(self.flame.xform[1].ispost(), False)
        self.assertEquals(self.flame.xform[2].ispost(), False)
        self.assertEquals(self.flame.xform[3].ispost(), False)
        self.assertEquals(self.flame.final.ispost(), False)

        self.assertEquals(self.flame.xform[0].post.ispost(), True)
        self.assertEquals(self.flame.xform[1].post.ispost(), True)
        self.assertEquals(self.flame.xform[2].post.ispost(), True)
        self.assertEquals(self.flame.xform[3].post.ispost(), True)
        self.assertEquals(self.flame.final.post.ispost(), True)

    def test_isfinal(self):
        self.assertEquals(self.flame.xform[0].isfinal(), False)
        self.assertEquals(self.flame.xform[1].isfinal(), False)
        self.assertEquals(self.flame.xform[2].isfinal(), False)
        self.assertEquals(self.flame.xform[3].isfinal(), False)
        self.assertEquals(self.flame.final.isfinal(), True)

        self.assertEquals(self.flame.xform[0].post.isfinal(), False)
        self.assertEquals(self.flame.xform[1].post.isfinal(), False)
        self.assertEquals(self.flame.xform[2].post.isfinal(), False)
        self.assertEquals(self.flame.xform[3].post.isfinal(), False)
        self.assertEquals(self.flame.final.post.isfinal(), False)

    def test_copy(self):
        x  = self.flame.xform[0]
        c = x.copy()

        self.assertTrue(x is not c)
        self.assertTrue(x.chaos is not c.chaos)
        self.assertTrue(x._parent is c._parent)
        self.assertTrue(x.chaos._parent is x)
        self.assertTrue(c.chaos._parent is c)
        self.assertTrue(x.post._parent is x)
        self.assertTrue(c.post._parent is c)

        self.assertEquals(c.index, 4)

        for key in x.__dict__:
            if key in ('_post', '_chaos'):
                continue

            self.assertEquals(getattr(x, key), getattr(c, key))

        c.delete()
        self.assertTrue(c not in self.flame.xform)

    def test_random(self):
        x = Xform.random(self.flame, fx=1)
        self.assertEquals(x, None)

        x = Xform.random(self.flame, fx=0)
        self.assertNotEquals(x, None)
        self.assertTrue(x in self.flame.xform)
        self.assertTrue(x.index, 5)
        x.delete()

        f = self.flame.final
        self.flame.final = None

        x = Xform.random(self.flame, fx=1)
        self.assertNotEquals(x, None)

        if x.isfinal():
            self.assertTrue(x is self.flame.final)
            self.assertEquals(x.index, None)
        else:
            self.assertTrue(x in self.flame.xform)
            self.assertEquals(x.index, 5)

        x.delete()

        self.flame.final = f

        x = Xform.random(self.flame, fx=0, ident=1)
        self.assertNotEquals(x, None)
        self.assertTrue(x in self.flame.xform)
        self.assertTrue(x.index, 5)

        #for k in x.list_variations():
        #    self.assertEquals(getattr(x, k), 1.0, '%s = %s' % (k, getattr(x, k)))

        x.delete()


        x = Xform.random(self.flame, fx=0, xw=1)
        self.assertNotEquals(x, None)
        self.assertTrue(x in self.flame.xform)
        self.assertTrue(x.index, 5)
        x.delete()


