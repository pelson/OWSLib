from unittest import TestCase
from lxml import etree
import owslib.gml.gml32 as gml


XML_template = """
<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:gmlrgrid="http://www.opengis.net/gml/3.3/rgrid">
{content}
</root>
""".strip()

DOMAINSET_EXAMPLE = """
<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:gml="http://www.opengis.net/gml/3.2">
<gml:domainSet>
  <gml:RectifiedGrid dimension="2" gml:id="GFS_Latest_ISBL_grid">
    <gml:limits>
      <gml:GridEnvelope>
        <gml:low>0 0</gml:low>
        <gml:high>719 360</gml:high>
      </gml:GridEnvelope>
    </gml:limits>
    <gml:axisName>x</gml:axisName>
    <gml:axisName>y</gml:axisName>
    <gml:origin>
      <gml:Point srsName="EPSG:4326" gml:id="GFS_Latest_ISBL_grid_origin">
        <gml:coordinates>0 -90</gml:coordinates>
      </gml:Point>
    </gml:origin>
    <gml:offsetVector srsName="EPSG:4326">0.5 7.0467596052536985</gml:offsetVector>
    <gml:offsetVector srsName="EPSG:4326">0 14.573944878270581</gml:offsetVector>
  </gml:RectifiedGrid>
</gml:domainSet>
</root>""".strip()


class TestGMLDomainSet(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        self.ds = gml.GMLdomainSet.from_xml(root[0], profiles=[gml.gml32_profile])

    def test_limits(self):
        envelope = self.ds.limits
        self.assertIsInstance(envelope, gml.GMLGridEnvelope)

    def test_axes(self):
        axes = self.ds.axes
        self.assertEqual(axes, ['x', 'y'])

    def test_origin(self):
        origin = self.ds.origin
        self.assertIsInstance(origin, gml.GMLPoint)

    def test_offset_vectors(self):
        offset_vectors = self.ds.offset_vectors
        for vector in offset_vectors:
            self.assertIsInstance(vector, gml.GMLVector)


class TestGMLRectifiedGrid(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        self.grid = gml.GMLdomainSet.from_xml(root[0], profiles=[gml.gml32_profile])
        self.assertIsInstance(self.grid, gml.GMLRectifiedGrid)

    def test_repr(self):
        self.assertEqual(repr(self.grid), '<GMLRectifiedGrid instance>')

    def test_attributes(self):
        self.assertIsInstance(self.grid.limits, gml.GMLGridEnvelope)
        self.assertEqual(self.grid.axes, ['x', 'y'])
        self.assertEqual(self.grid.dims, 2)
        self.assertIsInstance(self.grid.origin, gml.GMLPoint)
        self.assertIsInstance(self.grid.offset_vectors[0], gml.GMLVector)


class TestGMLVector(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        geom = gml.GMLdomainSet.from_xml(root[0], profiles=[gml.gml32_profile])
        self.vector = geom.offset_vectors[0]

    def test_repr(self):
        self.assertEqual(repr(self.vector), "GMLVector({}, [0.5, 7.0467596052536985])")

    def test_attributes(self):
        self.assertEqual(self.vector.components, [0.5, 7.0467596052536985])


class TestGMLEnvelope(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""
          <gml:Envelope axisLabels="Long Lat" srsDimension="2" srsName="CRS:84" uomLabels="deg deg">
            <gml:lowerCorner>-180 -90</gml:lowerCorner>
            <gml:upperCorner>180 90</gml:upperCorner>
          </gml:Envelope>
        """))
        self.envelope = gml.GMLEnvelope.from_xml(root[0], profiles=[gml.gml32_profile])

    def test_repr(self):
        self.assertEqual(repr(self.envelope),
                         "GMLEnvelope({'srsName': 'CRS:84', 'axisLabels': 'Long Lat', "
                                      "'uomLabels': 'deg deg', 'srsDimension': '2'}, "
                                     "lows=[-180.0, -90.0], highs=[180.0, 90.0])")

    def test_attributes(self):
        self.assertIsInstance(self.envelope.lows[0], float)
        self.assertEqual(self.envelope.lows, [-180.0, -90.0])
        self.assertEqual(self.envelope.highs, [180.0, 90.0])


class TestGMLTimePeriod(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""
          <gml:TimePeriod gml:id="tp_ForecastTimeRange_GFS_Latest_ISBL">
                <gml:beginPosition>2015-01-12T00:00:00Z</gml:beginPosition>
                <gml:endPosition>2015-01-20T00:00:00Z</gml:endPosition>
          </gml:TimePeriod>
        """))
        self.time_period = gml.GMLTimePeriod.from_xml(root[0], profiles=[gml.gml32_profile])

    def test_repr(self):
        self.assertEqual(repr(self.time_period),
                         "TimePeriod({'gml:id': 'tp_ForecastTimeRange_GFS_Latest_ISBL'}, datetime.datetime(2015, 1, 12, 0, 0), datetime.datetime(2015, 1, 20, 0, 0))")

    def test_attributes(self):
        from datetime import datetime
        self.assertEqual(self.time_period.attrs, {'gml:id': 'tp_ForecastTimeRange_GFS_Latest_ISBL'})
        self.assertEqual(self.time_period.start, datetime.strptime('2015-01-12T00:00:00Z', gml.GMLTimeFormat))
        self.assertEqual(self.time_period.end, datetime.strptime('2015-01-20T00:00:00Z', gml.GMLTimeFormat))


class TestGMLGridEnvelope(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        ds = gml.GMLdomainSet.from_xml(root[0], profiles=[gml.gml32_profile])
        self.envelope = ds.limits

    def test_repr(self):
        self.assertEqual(repr(self.envelope),
                         'GMLGridEnvelope({}, lows=[0, 0], highs=[719, 360])')

    def test_attributes(self):
        self.assertIsInstance(self.envelope.lows[0], int)
        self.assertEqual(self.envelope.lows, [0, 0])
        self.assertEqual(self.envelope.highs, [719, 360])


class TestGMLPoint(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        ds = gml.GMLdomainSet.from_xml(root[0], profiles=[gml.gml32_profile])
        self.point = ds.origin

    def test_repr(self):
        self.assertEqual(repr(self.point),
                         "GMLPoint({'gml:id': 'GFS_Latest_ISBL_grid_origin'}, [0.0, -90.0])")

    def test_attributes(self):
        self.assertIsInstance(self.point.coords[0], float)
        self.assertEqual(self.point.coords, [0.0, -90.0])


# Chapter 14

class TestGMLTimePosition(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""
          <gml:timePosition gml:id="wibble">2015-01-11T15:31:52Z</gml:timePosition>
        """))
        self.time = gml.GMLTimePosition.from_xml(root[0], profiles=[gml.gml32_profile])

    def test_repr(self):
        self.assertEqual(repr(self.time),
                         "GMLTimePosition({'gml:id': 'wibble'}, datetime.datetime(2015, 1, 11, 15, 31, 52))")

    def test_attributes(self):
        import datetime
        self.assertIsInstance(self.time.datetime, datetime.datetime)
        self.assertEqual(self.time.datetime, datetime.datetime(2015, 1, 11, 15, 31, 52))


class TestGMLRangeSet(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""""
        <gml:rangeSet><gml:DataBlock><gml:rangeParameters/><gml:tupleList>1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1</gml:tupleList></gml:DataBlock></gml:rangeSet>"""))
        self.range_set = gml.GMLRangeSet.from_xml(root[0], profiles=[gml.gml32_profile])

    def test_repr(self):
        self.assertEqual(repr(self.range_set),
                         "<GMLRangeSet instance>")

    def test_attributes(self):
        self.assertEqual(self.range_set.data.values, (['1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1'],))


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)