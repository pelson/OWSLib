from unittest import TestCase
from lxml import etree
import owslib.gml.gml33 as gml
import owslib.gml.gml32 as gml32


XML_template = """
<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:gmlrgrid="http://www.opengis.net/gml/3.3/rgrid">
{content}
</root>
""".strip()


class TestGMLReferenceableGridByArray(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""
        <gmlrgrid:ReferenceableGridByArray gml:id="ex" dimension="2"
            srsName="http://www.opengis.net/def/crs/EPSG/0/4326">
            <gml:limits>
                <gml:GridEnvelope>
                    <gml:low>0 0</gml:low>
                    <gml:high>4 5</gml:high>
                </gml:GridEnvelope>
            </gml:limits>
            <gml:axisLabels>x y</gml:axisLabels>
            <gml:posList>
            2 8 3 10 6 12 8 14 10 18
            4 6 6 8 8 12 10 14 12 16
            6 2 7 4 9 6 10 8 13 12
            8 2 8 3 10 5 11 8 13 10
            </gml:posList>
            <gml:sequenceRule axisOrder="+1 +2">Linear</gml:sequenceRule>
        </gmlrgrid:ReferenceableGridByArray>"""))
        self.grid = gml.GMLReferenceableGridByArray.from_xml(root[0], profiles=[gml.gml32.gml32_profile])

        root2 = etree.XML(XML_template.format(content="""
          <gml:ReferenceableGridByArray gml:id="6d-SO_t" dimension="3" uomLabels="DMSH DMSH metre" srsDimension="3"
           srsName="EPSG/0/4327">
            <gml:limits>
              <gml:GridEnvelope>
                <gml:low>0 0 0</gml:low>
                <gml:high>3 4 2</gml:high>
              </gml:GridEnvelope>
            </gml:limits>
            <gml:axisLabels>two 1 3</gml:axisLabels>
            <gml:posList>
              40   9.2 200   40.1 9.3 200   40.3 9.5 210
              40.1 9.3 205   40.3 9.5 220   40.4 9.7 225
              40.4 9.4 215   40.7 9.7 225   40.8 9.8 235
              40.6 9.5 220   40.8 9.7 230   40.9 9.9 240
        
              40.0 9.1 205   40.1 9.2 210   40.4 9.6 230
              40.2 9.5 220   40.2 9.4 240   40.7 9.7 240
              40.5 9.7 225   40.5 9.6 245   40.8 9.8 285
              40.7 9.8 230   40.6 9.8 290   41   10  295
            </gml:posList>
            <gml:sequenceRule axisOrder="+2 +1 +3">Linear</gml:sequenceRule>
          </gml:ReferenceableGridByArray>""".strip()))

        self.grid2 = gml.GMLReferenceableGridByArray.from_xml(root2[0], profiles=[gml.gml32.gml32_profile])

    def test_repr(self):
        self.assertEqual(repr(self.grid), '<GMLReferenceableGridByArray instance>')

    def test_attributes(self):
        self.assertIsInstance(self.grid.limits, gml32.GMLGridEnvelope)
        self.assertEqual(self.grid.axes, ['x', 'y'])
        self.assertEqual(self.grid.dims, 2)
        self.assertEqual(self.grid.pos_list[:12], [2.0, 8.0, 3.0, 10.0, 6.0, 12.0, 8.0, 14.0, 10.0, 18.0, 4.0, 6.0])
        self.assertEqual(self.grid.sequence_rule, ('+1 +2', 'Linear'))

    def test_ndarray(self):
        arrays1 = self.grid.np_arrays()
        self.assertIsInstance(arrays1, dict)
        self.assertEqual(sorted(arrays1.keys()), sorted(self.grid.axes))
        self.assertEqual(arrays1['y'].shape, (4, 1))
        self.assertEqual(arrays1['x'].shape, (1, 5))

    def test_ndarray_3d(self):
        arrays1 = self.grid2.np_arrays()
        self.assertEqual(arrays1['1'].shape, (1, 4, 1))
        self.assertEqual(list(arrays1['1'].flat), [9.2, 9.3, 9.4, 9.5])

        self.assertEqual(arrays1['two'].shape, (1, 1, 2))
        self.assertEqual(arrays1['3'].shape, (3, 1, 1))


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)